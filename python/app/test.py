# Databases - 2020/2021
# Final Project - REST API

# Authors:
#   David Valente Pereira Barros Leitão - 2019223148
#   João António Correia Vaz - 2019218159
#   Rodrigo Alexandre da Mota Machado - 2019218299

from datetime import datetime
from flask import Flask, json, jsonify, request, render_template
from psycopg2 import sql
import hashlib
import jwt
import logging, psycopg2

app = Flask(__name__)

@app.route('/')
def landing():
    return render_template('index.html')

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

    statement = """INSERT INTO db_user (email, username, pass) 
                VALUES (%s, %s, %s);"""
    with conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(statement, (email, username, password))
                logger.debug(f"Query {cursor.query} ")
                content['Status'] = 'Registered'
            except psycopg2.errors.UniqueViolation:
                content['Error'] = 'Username already in use'
    conn.close()

    return jsonify(content)
    
# Authenticate a user
@app.route('/dbproj/user', methods=['PUT'])
def authenticate():
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
    
    statement = "SELECT user_id, pass, valid FROM db_user WHERE username=%s"
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(statement, (username,))
            logger.debug(f"Query {cursor.query} returned {cursor.rowcount} rows")
            if cursor.rowcount == 1:
                row = cursor.fetchone()
                userId = row[0]
                hash = bytes(row[1])
                if row[2] == False:
                    content['Error'] = 'User is banned'
                elif password == hash:
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
    try:
        validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
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

    postmanFormat = "%a %b %d %Y %H:%M:%S %Z%z"
    regularFormat = "%d-%m-%Y %H:%M:%S"
    date = payload['ends']
    date = date[:date.find(" (")]
    date = datetime.strptime(date, postmanFormat)
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
    try:
        validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
    
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    content = dict()
    auctionSQL = """SELECT price, title, description, ends, username, 
                    min_price, auction_id, cancelled
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
                cancelled = row[7]
                ends = row[3]
                if cancelled:
                    content['Status'] = 'Cancelled'
                elif ends < datetime.now():
                    content['Status'] = 'Closed'
                else:
                    content['Status'] = 'Open'
                    content['Ends'] = row[3].strftime("%d-%m-%Y %H:%M:%S")
                content['Price'] = str(row[0])
                content['Title'] = row[1]
                content['Description'] = row[2]
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
    try:
        validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
    
    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    statement = """SELECT auction_id, description FROM auction 
                WHERE ends >= CURRENT_TIMESTAMP AND NOT cancelled"""

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
    try:
        validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
    
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
    try:
        token = validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
    
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

# Change auction details
@app.route('/dbproj/leilao/<leilaoId>', methods=['PUT'])
def changeAuction(leilaoId):
    logger.info(f"PUT /dbproj/leilao/{leilaoId}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    try:
        token = validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
        
    payload = request.get_json()
    present = set()
    if payload is not None:
        fields = set(payload.keys())
        accepted = {'title', 'description'}
        present = accepted.intersection(fields)
    if payload is None or len(present) == 0:
        return jsonify({'Error': 'Nothing to be done'})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})
    
    commonSQL = sql.SQL("UPDATE auction SET {fields} WHERE auction_id = %(auctionId)s")
    titleSQL = sql.SQL("title = %(title)s")
    descriptionSQL = sql.SQL("description = %(description)s")

    payload.update({'auctionId': leilaoId})
    logger.debug(payload)
    content = dict()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT seller FROM auction WHERE auction_id = %s", (leilaoId, ))
            if cursor.rowcount == 0:
                cursor.close()
                return jsonify({'Error': 'Auction not found'})
            if token.get('userId') != cursor.fetchone()[0]:
                cursor.close()
                return jsonify({'Error': 'Not seller'})
        with conn.cursor() as cursor:
            if ('title', 'description') in present:
                query = commonSQL.format(fields=sql.SQL(', ').join([titleSQL, descriptionSQL]))        
            elif 'title' in present:
                query = commonSQL.format(fields=titleSQL)
            elif 'description' in present:
                query = commonSQL.format(fields=descriptionSQL)
            
            try:
                cursor.execute(query, payload)
                logger.debug(cursor.query)
                content['Status'] = 'Success'
            except psycopg2.Error as e:
                logger.error(e.diag.message_primary)
                content['Error'] = 'Something went wrong'
    conn.close()
    
    return jsonify(content)

# Post a message
@app.route('/dbproj/message/<leilaoId>', methods=['POST'])
def postMessage(leilaoId):
    logger.info(f"POST /dbproj/message/{leilaoId}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    try:
        token = validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})

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
            try:
                cursor.execute("SELECT cancelled, ends FROM auction WHERE auction_id = %s", (leilaoId,))
                if cursor.rowcount == 0:
                    content['Error'] = 'Auction does not exist'
                else:
                    row = cursor.fetchone()
                    if row[0] == True:
                        content['Error'] = 'Auction has been cancelled'
                    elif row[1] < datetime.now():
                        content['Error'] = 'Auction has ended'
                    else:
                        statement = """INSERT INTO mural (auction_id, user_id, m_date, msg)
                                    VALUES (%(auctionId)s, %(userId)s, CURRENT_TIMESTAMP, %(message)s)"""
                        args = {'auctionId': leilaoId, 'userId': userId, 'message': msg}
                        
                        cursor.execute(statement, args)
                        content['Status'] = 'Success'
            except psycopg2.Error as e:
                logger.error(str(e))
                content['Erro'] = str(e)
    conn.close()

    return jsonify(content)

# Get user activity
@app.route('/dbproj/user/activity', methods=['GET'])
def activity():
    logger.info(f"POST /dbproj/user/activity")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    try:    
        token = validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})

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
    logger.info('GET /dbproj/user/notifications')
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    try:
        token = validate(authToken)
    except Exception as e:
        logger.debug(str(e))
        return jsonify({'Error': str(e)})
    
    logger.debug(f"userID {token.get('userId')}")
    statement = """SELECT n_date, msg, seen FROM notifs
                WHERE user_id = %(userId)s
                ORDER BY n_date DESC"""
    seen = "UPDATE notifs SET seen = true WHERE user_id = %(userId)s"

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    content = {'Seen': [], 'Unseen': []}
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(statement, token)
            for row in cursor:
                if row[2] == True:
                    content['Seen'].append({
                        "Date": row[0],
                        "Message": row[1]
                    })
                else:
                    content['Unseen'].append({
                        "Date": row[0],
                        "Message": row[1]
                    })
            try:
                cursor.execute(seen, token)
            except Exception as e:
                logger.error(str(e))
    conn.close()

    return jsonify(content)

@app.route('/dbproj/admin/cancel/<auctionId>', methods=['POST'])
def cancelAuction(auctionId):
    logger.info(f"POST /dbproj/leiloes/{auctionId}")
    authToken = request.headers.get('authToken')
    if authToken is None:
        return jsonify({'Error': 'Missing authToken'})
    try:
        token = validate(authToken, isAdmin=True)
    except Exception as e:
        logger.error(str(e))
        return jsonify({'Error': str(e)})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    check = "SELECT cancelled FROM auction WHERE auction_id = %s FOR UPDATE"
    statement = "UPDATE auction SET cancelled = true WHERE auction_id = %s"
    content = dict()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(check, (auctionId,))
            if cursor.rowcount == 0:
                content['Error'] = 'Auction does not exist'
            else:
                if cursor.fetchone()[0] == True:
                    content['Error'] = 'Auction already cancelled'
                else:
                    try:
                        cursor.execute(statement, (auctionId,))
                        content['Status'] = 'Success'
                    except psycopg2.Error as e:
                        logger.error(str(e))
                        content['Error'] = e.diag.message_primary
    conn.close()

    return jsonify(content)

@app.route('/dbproj/admin/stats', methods=['GET'])
def stats():
    logger.debug("GET /dbproj/admin/stats")
    authToken = request.headers.get('authToken')
    if authToken is None:
        logger.error("Missing authToken")
        return jsonify({'Error': 'Missing authToken'})
    try:
        token = validate(authToken, isAdmin=True)
    except Exception as e:
        logger.error(str(e))
        return jsonify({'Error': str(e)})

    conn = dbConn()
    if conn is None:
        return jsonify({'Error': 'Connection to db failed'})

    topSellers = """SELECT username, COUNT(*) as total FROM auction JOIN db_user
                    ON auction.seller = db_user.user_id
                    GROUP BY username ORDER BY total DESC
                    LIMIT 10"""
    topWinners = """SELECT username, COUNT(*) as total FROM auction FULL OUTER JOIN db_user
                    ON auction.last_bidder = db_user.user_id
                    WHERE ends < CURRENT_TIMESTAMP AND cancelled = false
                    GROUP BY username ORDER BY total DESC
                    LIMIT 10"""
    recentAuctions = """SELECT COUNT(*) as total FROM history
                        WHERE hist_id = 1 and hist_date BETWEEN CURRENT_TIMESTAMP - INTERVAL '863990 seconds'
                        AND CURRENT_TIMESTAMP + INTERVAL '863990 seconds'"""

    content = {'Sellers': [], 'Winners': []}
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(topSellers)
            logger.debug(f'Query {cursor.query} returned {cursor.rowcount} rows')
            for row in cursor:
                content['Sellers'].append({
                    'User': row[0],
                    'Auctions': row[1]
                })
            cursor.execute(topWinners)
            logger.debug(f'Query {cursor.query} returned {cursor.rowcount} rows')
            for row in cursor:
                content['Winners'].append({
                    'User': row[0],
                    'Won': row[1]
                })
            cursor.execute(recentAuctions)
            logger.debug(f'Query {cursor.query} returned {cursor.rowcount} rows')
            content['New Auctions'] = cursor.fetchone()[0]
    conn.close()

    return jsonify(content)

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

# Get JWT for user
def getToken(username, userId):
    payload = {'userId': userId, 'username': username}
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

# Read user token
def readToken(token):
    logger.debug(f"Decoding token {token}")
    try:
        decoded = jwt.decode(token, app.secret_key, algorithms='HS256') 
        logger.debug("Valid token")
    except jwt.InvalidSignatureError:
        logger.debug(f"Invalid token signature")
        decoded = None
    return decoded

# Token may be valid, but user not registered or banned
def validate(authToken, isAdmin=False):
    token = readToken(authToken)
    if token is None:
        raise Exception('Invalid token')

    conn = dbConn()
    if conn is None:
        raise Exception('Connection to db failed')

    commonSQL = sql.SQL("SELECT {fields} from db_user WHERE username = %s")
    cols = [sql.Identifier('user_id'), sql.Identifier('valid')]
    if isAdmin:
        cols.append(sql.Identifier('admin'))
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(commonSQL.format(fields=sql.SQL(', ').join(cols)), (token.get('username'),))
            if cursor.rowcount == 1:
                row = cursor.fetchone()
                if row[0] == token.get('userId'):
                    if row[1] == False:
                        raise Exception('User is banned')
                    if isAdmin and row[2] == False:
                        raise Exception('Not Admin')
                else:
                    raise Exception('User ID does not match')
            else:
                raise Exception('User does not exist')

    conn.close()

    return token

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
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    with open('secret/secret.key', 'rb') as f:
        app.secret_key = f.read()
        f.close()

    app.run(host='0.0.0.0', debug=True, threaded=True)
