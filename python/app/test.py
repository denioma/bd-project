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
                try:
                    cursor.execute("INSERT INTO db_user (email, username, pass) VALUES (%s, %s, %s);", 
                        (email, username, password))
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
    content = {'operation': 'authenticate a user'}
    payload = request.get_json()
    
    # Check for required request body fields
    required = {'username', 'password'}
    if set(payload.keys()).intersection(required) != required:
        content['error'] = 'pedido inválido'
        return jsonify(content)

    conn = dbConn()
    if conn is not None:
        username = payload['username']
        password = payload['password'].encode()
        password = hashlib.sha256(password).digest()
        logger.debug(f"Hash = {password}")
        sql = "SELECT pass FROM db_user WHERE username=%s"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (username,))
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount == 1:
                    row = cursor.fetchone()
                    hash = bytes(row[0])
                    logger.debug(f"Stored Hash: {hash}")
                    if password == hash:
                        logger.debug("Authenticated")
                        content['authenticated'] = 'true'
                        content['authToken'] = getToken(username)
                    else:
                        logger.debug("Authentication failed")
                        content['authenticated'] = 'false'
                else: content['erro'] = 'user does not exist'
        conn.close()
    else: content['erro'] = 'Connection to db failed'
    content['payload'] = dict()
    for key in required:
        content['payload'].update({key: payload[key]})
    return jsonify(content)

# Create a new auction
@app.route('/dbproj/leilao', methods=['POST'])
def newAuction():
    logger.info("POST /dbproj/leilao")
    content = {'operation': 'create a new auction'}
    payload = request.get_json()
    
    # Check for required request body fields
    required = {'artigoId', 'precoMinimo', 'titulo', 'descricao', 'ends', 'authToken'}
    fields = set(payload.keys())
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'Error': f'Missing fields {diff}'})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    # TODO Criar um leilão na DB
    token = readToken(payload['authToken'])
    content['payload'] = dict()
    for key in required:
        if key != 'jwt': content['payload'].update({key: payload[key]})
    date = payload['ends']
    date = date[:date.find(" (")]
    content['payload']['ends'] = date
    date = datetime.strptime(date, "%a %b %d %Y %H:%M:%S %Z%z")
    sql = """INSERT INTO auction (seller, itemid, minprice, price, title, description, ends) VALUES 
      (%(seller)s, %(artigoId)s, %(precoMinimo)s, %(precoMinimo)s, %(titulo)s, %(descricao)s, %(ends)s)"""
    args = {'seller': token['username']}
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
            except psycopg2.DataError:
                content['error'] = 'DB Exception: DataError'
    conn.close()
    return jsonify(content)

# TODO Get auction details
@app.route('/dbproj/leilao/<leilaoId>', methods=['GET'])
def getAuction(leilaoId):
    logger.info(f"GET /dbproj/leilao/{leilaoId}")
    payload = request.get_json()
    if 'authToken' not in payload.keys():
        return jsonify({'Error': 'Missing authToken'})
    
    content = {'operation': 'get auction details', 'leilaoId': leilaoId}
    conn = dbConn()
    if conn is not None:
        auctionSQL = """SELECT price, title, description, ends, seller_db_user_username 
                        FROM auction WHERE itemid = %s;"""
        historySQL = """SELECT buyer_db_user_username, bid_date, price 
                        FROM bid WHERE auction_itemid = %s ORDERED BY bid_date;"""
        messageSQL = "SELECT * FROM comment WHERE auction_itemid = %s ORDERED BY c_date;"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(auctionSQL, (leilaoId,))
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount > 0:
                    row = cursor.fetchone()
                    logger.debug(f"{row}")
                    content['price'] = row[0]
                    content['title'] = row[1]
                    content['description'] = row[2]
                    content['ends'] = row[3]
                    content['seller'] = row[4]
                    cursor.execute(historySQL, (leilaoId,))
                    logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                    if cursor.rowcount > 0:
                        content['history'] = []
                        for row in cursor:
                            logger.debug(f"{row}")
                            content['history'].append({
                                'bidder': row[0],
                                'timestamp': row[1],
                                'bid': row[2]
                            })
                    cursor.execute(messageSQL, (leilaoId,))
                    logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                    if cursor.rowcount > 0:
                        content['messages'] = []
                        for row in cursor:
                            # TODO change db structure to include commenter
                            logger.debug(f"{row}")
                            content['messages'].append({
                                'msg': row[1],
                                'date': row[0]
                            })
                else:
                    content['erro'] = 'Auction not found'
        conn.close()
    else: content['erro'] = 'Connection to db failed'
    return jsonify(content)

# List all open auctions
@app.route('/dbproj/leiloes', methods=['GET'])
def listAuctions():
    logger.info("GET /dbproj/leiloes")
    content = {'operation': 'list all open auctions'}
    conn = dbConn()
    if conn is not None:
        sql = "SELECT auction.itemid, auction.description FROM auction"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                content['result'] = []
                if cursor.rowcount > 0:
                    for row in cursor:
                        logger.debug(f"{row}")
                        content['result'].append({'leilaoId': row[0], 'description': row[1]})
                else: content['result'] = 'no results'
        conn.close()
    return jsonify(content)

# Search on open auctions
@app.route('/dbproj/leiloes/<keyword>', methods=['GET'])
def searchAuctions(keyword):
    logger.info(f"GET /dbproj/leiloes/{keyword}")
    content = {'Operation': 'Search for open auction', 'Keyword': keyword}
    conn = dbConn()
    if conn is not None:
        with conn:
            # TODO Uncomment full query after changing itemid to VARCHAR
            # sql = """SELECT auction.itemid, auction.description
            #         FROM auction WHERE auction.itemid = %(keyword)s 
            #         OR auction.description LIKE %(regex)s"""
            sql = """SELECT auction.itemid, auction.description
                    FROM auction WHERE auction.description like %(regex)s
                    ORDER BY auction.itemid"""
            with conn.cursor() as cursor:
                cursor.execute(sql, {'keyword': keyword, 'regex': f'%{keyword}%'})
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                if cursor.rowcount > 0: 
                    content['Results'] = cursor.fetchall()
                else: 
                    content = {'Error': 'No results found'}
        conn.close()
    else: 
        content['Error'] = 'Connection to database failed'
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
def getToken(username):
    payload = {'username': username}
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