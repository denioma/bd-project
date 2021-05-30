# Databases - 2020/2021
# Final Project - REST API

# Authors:
#   David Valente Pereira Barros Leitão - 2019223148
#   João António Correia Vaz - 2019218159
#   Rodrigo Alexandre da Mota Machado - 2019218299

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
    logger.info("POST /dbproj/user")
    payload = request.get_json()
    required = {'username', 'password', 'email'}    
    fields = set(payload.keys())
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'Error': f'Missing fields {diff}'})
    
    username = payload['username']
    email = payload['email']
    password = payload['password']
    password = password.encode()
    # TODO Change password hashing to a more secure scheme
    password = hashlib.sha256(password).digest()
    content = dict()
    
    conn = dbConn()
    if conn is None:
        pass

    statement = """INSERT INTO db_user (email, username, pass, user_id) 
                VALUES (%s, %s, %s, %s);"""
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM db_user;")
            logger.debug(cursor.query)
            user_id = cursor.fetchone()[0] + 1
            logger.debug(f"User ID {user_id}")
            try:
                cursor.execute(statement, (email, username, password, user_id))
                logger.debug(f"Query {cursor.query} ")
                content['Status'] = 'Registered'
            except psycopg2.errors.UniqueViolation:
                content['Error'] = 'Username already in use'
    conn.close()

    return jsonify(content)
    
# Authenticate a user
@app.route('/dbproj/user', methods=['PUT'])
def auth():
    logger.info("PUT /dbproj/user")
    payload = request.get_json()
    fields = set(payload.keys())
    
    # Check for required request body fields
    required = {'username', 'password'}
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'Error': f'Missing fields {diff}'})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    content = dict()
    username = payload['username']
    password = payload['password'].encode()
    password = hashlib.sha256(password).digest()
    statement = "SELECT user_id, pass FROM db_user WHERE username=%s"
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(statement, (username,))
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
    
    return jsonify(content)

# Create a new auction
@app.route('/dbproj/leilao', methods=['POST'])
def newAuction():
    logger.info("POST /dbproj/leilao")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    if readToken(authToken) is None:
        return jsonify({'Error': 'Invalid authToken'})
    required = {'artigoId', 'precoMinimo', 'titulo', 'descricao', 'ends'}
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

    date = payload['ends']
    date = date[:date.find(" (")]
    date = datetime.strptime(date, "%a %b %d %Y %H:%M:%S %Z%z")
    authToken = readToken(authToken)

    statement = """INSERT INTO auction (item_id, seller, min_price, price, title, description, ends)
                VALUES (%(artigoId)s, %(seller)s, %(precoMinimo)s, %(precoMinimo)s, %(titulo)s, %(descricao)s, %(ends)s)
                RETURNING auction_id"""
    
    args = {'seller': authToken['userId'], 'artigoId': payload['artigoId'], 'precoMinimo': payload['precoMinimo'],
            'titulo': payload['titulo'], 'descricao': payload['descricao'], 'ends': date}
    logger.debug(args)
    
    with conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(statement, args)
                logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
                leilaoId = cursor.fetchone()[0]
                logger.debug(f"New auctionId = {leilaoId}")
                content['leilaoId'] = leilaoId
            except psycopg2.DataError as e:
                content['Error'] = 'DB Exception'
                logger.error(e.pgerror)
    conn.close()

    return jsonify(content)

@app.route('/dbproj/leilao/<leilaoId>', methods=['GET'])
def getAuction(leilaoId):
    logger.info(f"GET /dbproj/leilao/{leilaoId}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    if readToken(authToken) is None:
        return jsonify({'Error': 'Invalid authToken'})
    
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    content = dict()
    auctionSQL = """SELECT price, title, description, ends, username, 
                    min_price, auction_id
                    FROM auction INNER JOIN db_user 
                    ON auction.seller = db_user.user_id
                    WHERE auction_id = %s;"""
    historySQL = """SELECT username, bid_date, price 
                    FROM bid INNER JOIN db_user
                    ON bid.bidder = db_user.user_id                  
                    WHERE auction_id = %s ORDER BY bid_date;"""
    messageSQL = """SELECT username, m_date, msg 
                    FROM mural JOIN db_user
                    ON mural.user_id = db_user.user_id
                    WHERE auction_id = %s ORDER BY m_date;"""

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
                content['Starting Price'] = str(row[5])
                content['Auction ID'] = row[6]
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
                            'User': row[0],
                            'Date': row[1].strftime("%d-%m-%Y %H:%M:%S"),
                            'Message': row[2]
                        })
    conn.close()

    return jsonify(content)

# List all open auctions
@app.route('/dbproj/leiloes', methods=['GET'])
def listAuctions():
    logger.info("GET /dbproj/leiloes")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    if readToken(authToken) is None:
        return jsonify({'Error': 'Invalid authToken'})
    
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    statement = """SELECT auction_id, description FROM auction 
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
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    if readToken(authToken) is None:
        return jsonify({'Error': 'Invalid authToken'})
    
    content = {'Operation': 'Search for open auction', 'Keyword': keyword}
    conn = dbConn()

    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    statement = """SELECT auction.item_id, auction.description
                FROM auction WHERE auction.item_id = %(keyword)s 
                OR auction.description LIKE %(regex)s"""

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(statement, {'keyword': keyword, 'regex': f'%{keyword}%'})
            logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
            if cursor.rowcount > 0: 
                content = []
                for row in cursor:
                    content.append({'itemId': row[0], 'description': row[1]})
            else: 
                content = {'Error': 'No results found'}
    conn.close()

    return jsonify(content)

# Bid on an open auction
# TODO Stop bid on seller's own listing
@app.route('/dbproj/licitar/leilao/<leilaoId>/<licitacao>', methods=['GET'])
def bidAuction(leilaoId, licitacao):
    logger.info(f"GET /dbproj/licitar/leilao/{leilaoId}/{licitacao}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    token = readToken(authToken)
    if authToken is None:
        return jsonify({'Error': 'Invalid authToken'})
    
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    userId = token.get('userId')
    statement = """INSERT INTO bid (auction_id, bid_id, bid_date, price, bidder) 
                VALUES (%(auctionId)s, %(bidId)s, current_timestamp, %(price)s, %(bidder)s)"""
    content = dict()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*)+1 FROM bid WHERE bidder = %s", (userId,))
            bidId = cursor.fetchone()[0]
            args = {'auctionId': leilaoId, 'price': licitacao, 'bidder': userId, 'bidId': bidId}
            try:
                cursor.execute(statement, args)
                content['Status'] = 'Success'
            except psycopg2.Error as e:
                logger.debug(e.diag.message_primary)
                content['Error'] = e.diag.message_primary
    conn.close()
    
    return jsonify(content)

# TODO Change an auction's details
@app.route('/dbproj/leilao/<leilaoId>', methods=['PUT'])
def changeAuction(leilaoId):
    logger.info(f"PUT /dbproj/leilao/{leilaoId}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    token = readToken(authToken)
    if token is None:
        return jsonify({'Error': 'Invalid authToken'})
        
    payload = request.get_json()
    fields = set(payload.keys())

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    with conn:
        with conn.cursor() as cursor:
            pass
    conn.close()
    
    return jsonify({'Error': 'Not yet implemented'})

# Post a message
@app.route('/dbproj/message/<leilaoId>', methods=['POST'])
def postMessage(leilaoId):
    logger.info(f"POST /dbproj/message/{leilaoId}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    token = readToken(authToken)
    if token is None:
        return jsonify({'Error': 'Invalid authToken'})

    payload = request.get_json()
    required = {'message'}
    fields = set(payload.keys())
    diff = list(required.difference(fields))
    if len(diff) > 0:
        return jsonify({'Error': f'Missing body fields: {diff}'})
    msg = payload['message']
    
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    content = dict()
    with conn:
        userId = token.get('userId')
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*)+1 FROM mural WHERE user_id = %s", (userId,))
            msgId = cursor.fetchone()[0]

            statement = """INSERT INTO mural (m_id, item_id, user_id, m_date, msg)
                        VALUES (%(msgId)s, %(itemId)s, %(userId)s, CURRENT_TIMESTAMP, %(message)s)"""
            args = {'msgId': msgId, 'itemId': leilaoId, 'userId': userId, 'message': msg}
            
            cursor.execute(statement, args)
            content['Status'] = 'Success'
    
    conn.close()

    return jsonify(content)

# Get user activity
@app.route('/dbproj/user/activity', methods=['GET'])
def activity():
    logger.info(f"POST /dbproj/user/activity")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    token = readToken(authToken)
    if token is None:
        return jsonify({'Error': 'Invalid authToken'})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    sellerSQL = """SELECT auction.auction_id, auction.title, auction.description 
                FROM auction WHERE auction.seller = %(userId)s ORDER BY auction_id"""
    bidderSQL = """SELECT auction.auction_id, auction.title, auction.description 
                FROM auction JOIN bid ON bid.auction_id = auction.auction_id
                WHERE bid.bidder = %(userId)s ORDER BY auction_id"""

    content = {'Seller': [], 'Bidder': []}
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sellerSQL, token)
            for row in cursor:
                content['Seller'].append({
                    'Auction ID': row[0],
                    'Title': row[1],
                    'Description': row[2]
                })
            cursor.execute(bidderSQL, token)
            for row in cursor:
                content['Bidder'].append({
                    'Auction ID': row[0],
                    'Title': row[1],
                    'Description': row[2]
                })
    conn.close()
        
    return jsonify(content)

@app.route('/dbproj/user/notifications', methods=['GET'])
def notifications():
    pass

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