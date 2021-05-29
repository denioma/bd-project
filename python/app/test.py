from datetime import datetime
from flask import Flask, json, jsonify, request, render_template
import hashlib
import jwt
import logging, time, psycopg2

app = Flask(__name__)

@app.route('/')
def landing():
    return """Welcome to the Auction House!<br>
            I have a splitting headache"""

@app.route("/dbproj/user", methods=['POST'])
def register():
    logger.info("POST /dbproj/users")
    content = {'operation': 'register a user'}
    payload = request.get_json()
    
    # Check for required request body fields
    required = {'username', 'password', 'email'}    
    if set(payload.keys()).intersection(required) != required:
        content['error'] = 'pedido inválido'
        return jsonify(content)
    
    content['payload'] = dict()
    for key in required:
        content['payload'].update({key: payload[key]})
    username = payload['username']
    email = payload['email']
    password = payload['password']
    password = password.encode()
    # TODO Change password hashing to a more secure scheme
    password = hashlib.sha256(password).digest()
    logger.debug(f"Hash = {password}")
    conn = dbConn()
    if conn is not None:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM db_user;")
                logger.debug(cursor.query)
                user_id = cursor.fetchone()[0] + 1
                logger.debug(f"User ID {user_id}")
                try:
                    cursor.execute("INSERT INTO db_user (email, username, pass, user_id) VALUES (%s, %s, %s, %s);", 
                        (email, username, password, user_id))
                    logger.debug(f"Query {cursor.query} ")
                    content['status'] = 'registered'
                except psycopg2.errors.UniqueViolation:
                    content['erro'] = 'username already in use'
        conn.close()
    return jsonify(content)
    
# Authenticate a user
@app.route('/dbproj/user', methods=['PUT'])
def auth():
    logger.info("PUT /dbproj/user")
    payload = request.get_json()
    fields = set(payload.keys())
    content = dict()
    
    # Check for required request body fields
    required = {'username', 'password'}
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'Error': f'Missing fields {diff}'})

    conn = dbConn()
    if conn is not None:
        username = payload['username']
        password = payload['password'].encode()
        password = hashlib.sha256(password).digest()
        sql = "SELECT user_id, pass FROM db_user WHERE username=%s"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (username,))
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount == 1:
                    row = cursor.fetchone()
                    userId = row[0]
                    hash = bytes(row[1])
                    if password == hash:
                        logger.debug("Authenticated")
                        content['authToken'] = getToken(username, userId)
                    else:
                        logger.debug("Authentication failed")
                        content['Error'] = 'Wrong password'
                else: content['Error'] = 'User does not exist'
        conn.close()
    else: content['Error'] = 'Connection to db failed'
    return jsonify(content)

# Create a new auction
@app.route('/dbproj/leilao', methods=['POST'])
def newAuction():
    logger.info("POST /dbproj/leilao")
    required = {'artigoId', 'precoMinimo', 'titulo', 'descricao', 'ends', 'authToken'}
    payload = request.get_json()
    if payload is None:
        return jsonify({'Error': f'Missing fields {required}'})
    content = dict()
    fields = set(payload.keys())
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'Error': f'Missing fields {diff}'})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    token = readToken(payload['authToken'])
    date = payload['ends']
    date = date[:date.find(" (")]
    date = datetime.strptime(date, "%a %b %d %Y %H:%M:%S %Z%z")
    sql = """INSERT INTO auction (seller, item_id, min_price, price, title, description, ends) VALUES 
      (%(seller)s, %(artigoId)s, %(precoMinimo)s, %(precoMinimo)s, %(titulo)s, %(descricao)s, %(ends)s)"""
    args = {'seller': token['userId']}
    for key in required:
        if key != 'ends':
            args.update({key: payload[key]})
    args.update({'ends': date})
    logger.debug(args)
    with conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, args)
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                content['Status'] = 'Success'
            except psycopg2.DataError as e:
                content['Error'] = 'DB Exception'
                logger.error(e.pgerror)
    conn.close()
    return jsonify(content)

# TODO Test Bid History and Mural
@app.route('/dbproj/leilao/<leilaoId>', methods=['GET'])
def getAuction(leilaoId):
    logger.info(f"GET /dbproj/leilao/{leilaoId}")
    payload = request.get_json()
    content = dict()
    if payload is None or 'authToken' not in payload.keys():
        return jsonify({'Error': 'Missing authToken'})
    
    conn = dbConn()
    if conn is None:
        return jsonify({'erro': 'Connection to db failed'})

    auctionSQL = """SELECT price, title, description, ends, username 
                    FROM auction INNER JOIN db_user 
                    ON auction.seller = db_user.user_id
                    WHERE item_id = %s;"""
    historySQL = """SELECT username, b_date, price 
                    FROM bid INNER JOIN db_user
                    ON bid.bidder = db_user.user_id                  
                    WHERE item_id = %s ORDER BY b_date;"""
    messageSQL = """SELECT username, m_date, msg 
                    FROM mural JOIN db_user
                    ON mural.user_id = db_user.user_id
                    WHERE item_id = %s ORDER BY m_date;"""

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(auctionSQL, (leilaoId,))
            logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
            if cursor.rowcount == 0:
                content['Error'] = 'Auction not found'
            else:
                row = cursor.fetchone()
                logger.debug(f"{row}")
                content['Price'] = str(row[0])
                content['Title'] = row[1]
                content['Description'] = row[2]
                content['Ends'] = row[3].strftime("%d-%m-%Y %H:%M:%S")
                content['Seller'] = row[4]
                cursor.execute(historySQL, (leilaoId,))
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount == 0:
                    content['History'] = 'Empty'
                else:
                    content['History'] = []
                    for row in cursor:
                        logger.debug(f"{row}")
                        content['History'].append({
                            'Bidder': row[0],
                            'Timestamp': row[1].strftime("%d-%m-%Y %H:%M:%S"),
                            'Bid': str(row[2])
                        })
                cursor.execute(messageSQL, (leilaoId,))
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount == 0:
                    content['Mural'] = 'Empty'
                else:
                    content['Mural'] = []
                    for row in cursor:
                        logger.debug(f"{row}")
                        content['Mural'].append({
                            'Message': row[1],
                            'Timestamp': row[0].strftime("%d-%m-%Y %H:%M:%S")
                        })
    conn.close()

    return jsonify(content)

# List all open auctions
@app.route('/dbproj/leiloes', methods=['GET'])
def listAuctions():
    logger.info("GET /dbproj/leiloes")
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    statement = """SELECT item_id, description FROM auction 
                WHERE ends >= CURRENT_TIMESTAMP"""

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(statement)
            logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
            if cursor.rowcount == 0:
                content = {'Error': 'No results'}
            else:
                content = []
                for row in cursor:
                    logger.debug(f"{row}")
                    content.append({'auctionId': row[0], 'description': row[1]})
    conn.close()

    return jsonify(content)

# Search on open auctions
@app.route('/dbproj/leiloes/<keyword>', methods=['GET'])
def searchAuctions(keyword):
    logger.info(f"GET /dbproj/leiloes/{keyword}")
    content = {'Operation': 'Search for open auction', 'Keyword': keyword}
    conn = dbConn()

    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    # TODO decide wether itemId is a Integer or Varchar
    sql = """SELECT auction.item_id, auction.description
            FROM auction WHERE auction.item_id = %(keyword)s 
            OR auction.description LIKE %(regex)s"""

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, {'keyword': keyword, 'regex': f'%{keyword}%'})
            logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
            if cursor.rowcount > 0: 
                content = []
                for row in cursor:
                    content.append({'auctionId': row[0], 'description': row[1]})
            else: 
                content = {'Error': 'No results found'}
    conn.close()

    return jsonify(content)

# Bid on an open auction
@app.route('/dbproj/licitar/leilao/<leilaoId>/<licitacao>', methods=['GET'])
def bidAuction(leilaoId, licitacao):
    logger.info(f"GET /dbproj/licitar/leilao/{leilaoId}/{licitacao}")
    required = {'jwt'}
    payload = request.get_json()
    fields = set(payload.keys())
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'erro': 'missing auth token'})
    content = {'operation': 'bid on open auction', 'leilaoId': leilaoId, 'licitacao': licitacao}
    conn = dbConn()
    if conn is not None:
        username = readToken(payload['jwt'])['username']
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT price FROM auction WHERE itemid = %s;", (leilaoId,))
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount == 1:
                    currentPrice = cursor.fetchone()[0]
                    if licitacao <= currentPrice:
                        content['erro'] = 'Bid is lower than current price'
                    else:
                        statement = """INSERT INTO bid (itemid, b_date, price, bidder) 
                        VALUES (
                            %(itemid)s, 
                            current_timestamp, 
                            %(price)s,
                            %(bidder)s)
                        """
                        try:
                            cursor.execute(statement, (leilaoId, licitacao, username))
                            content['status'] = 'Sucess'
                        except psycopg2.Error as e:
                            logger.debug(e.diag.message_primary)
                else: content['erro'] = 'Auction not found'
        conn.close()
    else: content['erro'] = 'Connection to db failed'
    return jsonify(content)

# Change an auctions details
@app.route('/dbproj/leilao/<leilaoId>', methods=['PUT'])
def changeAuction(leilaoId):
    logger.info(f"PUT /dbproj/leilao/{leilaoId}")
    payload = request.get_json()
    content = {'operation': 'change auction details', 'leilaoId': leilaoId, 
        'erro': 'not yet implemented', 'payload': payload}
    return jsonify(content)

# Post a message
@app.route('/dbproj/message/<leilaoId>', methods=['POST'])
def postMessage(leilaoId):
    logger.info(f"POST /dbproj/message/{leilaoId}")
    payload = request.get_json()
    required = {'jwt', 'message'}
    fields = set(payload.keys())
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'erro': f'missing body fields: {diff}'})
    jwt = payload['jwt']
    msg = payload['message']
    token = readToken(jwt)
    conn = dbConn()
    if conn is not None:
        return jsonify({'erro': 'not yet implemented'})
        """
        with conn:
            with conn.cursor() as cursor:
                pass
            conn.close()
        """
    else: return jsonify({'erro': 'connection to db failed'})
    

# Not so hidden easter egg
@app.route('/bangers')
def banger1():
    return render_template("gift.html")

# Connect to db
def dbConn():
    try:
        connection = psycopg2.connect(user='admin', password='projadmin', host='db', port='5432', database='auctions')
    except psycopg2.DatabaseError as e:
        logger.error(e.diag.message_primary)
        connection = None
    return connection

def getKey():
    with open("secret/secret.key", "rb") as f:
        key = f.read()
        f.close()
    return key

# Get JWT for user
def getToken(username, userId):
    payload = {'userId': userId, 'username': username}
    return jwt.encode(payload, getKey(), algorithm='HS256')

# Read user token
def readToken(token):
    logger.debug(f"Decoding token {token}")
    try:
        decoded = jwt.decode(token, getKey(), algorithms='HS256') 
        logger.debug("Valid token")
    except jwt.InvalidSignatureError:
        logger.debug(f"Invalid token signature")
        decoded = None
    return decoded

def getUserId(username):
    conn = dbConn()
    if conn is None:
        return None
    with conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT user_id FROM db_user WHERE username = %s", (username,))
            except psycopg2.Error as e:
                logger.debug(e.diag.primary_message)
                return None
            userId = cursor.fetchone()[0]
    conn.close()
    return userId

##########################
#          Main          #
##########################
if __name__ == '__main__':
    # Logger setup
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Logger formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    app.run(host='0.0.0.0', debug=True, threaded=True)