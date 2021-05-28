from datetime import datetime
from flask import Flask, json, jsonify, request, render_template
# from cryptography.fernet import Fernet
# import jwt
import logging, time, psycopg2

app = Flask(__name__)

@app.route('/')
def landing():
    return 'Welcome to the Auction House!'

# TODO Register a user in the DB
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
    # TODO Registar utilizador na DB e retornar userId/mensagem de erro
    username = payload['username']
    email = payload['email']
    # password = encrypt(bytes(payload['password'], 'utf-8'))
    password = payload['password']
    conn = dbConn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO db_user (email, username, password) VALUES (%s, %s, %s);", 
        (email, username, password))
    conn.commit()
    conn.close()
    return jsonify(content)
    
# TODO Authenticate a user
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

    content['error'] = 'not yet implemented'
    content['payload'] = dict()
    for key in required:
        content['payload'].update({key: payload[key]})
    return jsonify(content)

# Create a new auction
@app.route('/dbproj/leilao', methods=['POST'])
def newAuction():
    logger.info("POST /dbproj/leilao")
    content = {'operation': 'create a new auction'}
    payload = request.get_json();

    # Check for required request body fields
    required = {'artigoId', 'precoMinimo', 'titulo', 'descricao', 'ends'}
    if set(payload.keys()).intersection(required) != required:
        content['error'] = 'pedido inválido'
        return jsonify(content)

    # TODO Criar um leilão na DB
    content['payload'] = dict()
    for key in required:
        content['payload'].update({key: payload[key]})
    """
    date = payload['ends']
    date = date[:date.find(" (")]
    content['payload']['ends'] = date
    date = datetime.strptime(date, "%a %b %d %Y %H:%M:%S %Z%z")
    """
    # sql = """INSERT INTO auction VALUES 
    #   (%%(artigoId)s, %%(precoMinimo)s, %%(preco)s, %%(titulo)s, %%(descricao)s, %%(ends)s)"""
    """
    args = {}
    for key in required:
        if key != 'ends': 
            args.update({key, payload[key]})
    conn = dbConn()
    if conn is not None:
        with conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, ())
                except psycopg2.DataError:
                    content['error'] = 'DB Exception: DataError'
        conn.close()
    else content['error'] = "Connection to db failed"
    """
    content['error'] = 'not yet implemented'
    return jsonify(content)

# TODO Get auction details
@app.route('/dbproj/leilao/<leilaoId>', methods=['GET'])
def getAuction(leilaoId):
    logger.info(f"GET /dbproj/leilao/{leilaoId}")
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
                if cursor.rowcount > 0:
                    row = cursor.fetchone()
                    logger.debug(f"{row}")
                    content['price'] = row[0]
                    content['title'] = row[1]
                    content['description'] = row[2]
                    content['ends'] = row[3]
                    content['seller'] = row[4]
                    cursor.execute(historySQL, (leilaoId,))
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
        sql = "SELECT auction.itemid, auction.description FROM auction;"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
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
    content = {'operation': 'search for open auction', 'keyword': keyword}
    conn = dbConn()
    if conn is not None:
        with conn:
            sql = """SELECT auction.itemid, auction.description
                    FROM auction WHERE auction.itemid = %(keyword)s 
                    OR auction.description like '%%%(keyword)s%%'"""
            with conn.cursor() as cursor:
                cursor.execute(sql, {'keyword': keyword})
                pass
        conn.close
    else: content['erro'] = 'Connection to db failed'
    return jsonify(content)

# Bid on an open auction
@app.route('/dbproj/licitar/leilao/<leilaoId>/<licitacao>', methods=['GET'])
def bidAuction(leilaoId, licitacao):
    logger.info(f"GET /dbproj/licitar/leilao/{leilaoId}/{licitacao}")
    content = {'operation': 'bid on open auction', 'leilaoId': leilaoId, 'licitacao': licitacao}
    conn = dbConn()
    if conn is not None:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT price FROM auction WHERE itemid = %s;", (leilaoId,))
                if cursor.rowcount == 1:
                    currentPrice = cursor.fetchone()[0]
                    if licitacao <= currentPrice:
                        content['erro'] = 'Bid is lower than current price'
                    else:
                        # TODO bid on an auction
                        content['erro'] = 'not yet implemented'
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

"""
def getKey():
    with open("secret/fernet", "rb") as f:
        key = f.read()
        f.close()
    return key

def encrypt(data):
    f = Fernet(getKey())
    return f.encrypt(data)

def decrypt(data):
    f = Fernet(getKey())
    return f.decrypt(data)
"""

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