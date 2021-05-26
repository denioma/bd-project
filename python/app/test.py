from flask import Flask, json, jsonify, request
import logging, time, psycopg2

app = Flask(__name__)

@app.route('/')
def landing():
    return 'Welcome to the Auction House!'

# Register a user in the DB
@app.route("/dbproj/user", methods=['POST'])
def register():
    content = {'operation': 'register a user'}
    payload = request.get_json()
    
    # Check for required request body fields
    required = {'username', 'password', 'email'}    
    if set(payload.keys()).intersection(required) != required:
        content['error'] = 'pedido inválido'
        return jsonify(content)
    
    # TODO Registar utilizador na DB e retornar userId/mensagem de erro
    content['error'] = 'not yet implemented'
    content['payload'] = dict()
    for key in required:
        content['payload'].update({key: payload[key]})
    return jsonify(content)
    
# Authenticate a user
@app.route('/dbproj/user', methods=['PUT'])
def auth():
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
    content = {'operation': 'create a new auction'}
    payload = request.get_json();

    # Check for required request body fields
    required = {'artigoId', 'precoMinimo', 'titulo', 'descricao', 'ends'}
    if set(payload.keys()).intersection(required) != required:
        content['error'] = 'pedido inválido'
        return jsonify(content)

    # TODO Criar um leilão na DB
    content['error'] = 'not yet implemented'
    content['payload'] = dict()
    for key in required:
        content['payload'].update({key: payload[key]})
    return jsonify(content)

# Get auction details
@app.route('/dbproj/leilao/<leilaoId>', methods=['GET'])
def getAuction(leilaoId):
    content = {'operation': 'get auction details', 'leilaoId': leilaoId, 
        'erro': 'not yet implemented'}
    return jsonify(content)

# List all open auctions
@app.route('/dbproj/leiloes', methods=['GET'])
def listAuctions():
    content = {'operation': 'list all open auctions', 'erro': 'not yet implemented'}
    return jsonify(content)

# Search on open auctions
@app.route('/dbproj/leiloes/<keyword>', methods=['GET'])
def searchAuctions(keyword):
    content = {'operation': 'search for open auction', 'keyword': keyword, 
        'erro': 'not yet implemented'}
    return jsonify(content)

# Bid on an open auction
@app.route('/dbproj/licitar/leilao/<leilaoId>/<licitacao>', methods=['GET'])
def bidAuction(leilaoId, licitacao):
    content = {'operation': 'bid on open auction', 'leilaoId': leilaoId, 'licitacao': licitacao, 
        'erro': 'ot yet implemented'}
    return jsonify(content)

# Change an auctions details
@app.route('/dbproj/leilao/<leilaoId>', methods=['PUT'])
def changeAuction(leilaoId):
    payload = request.get_json()
    content = {'operation': 'change auction details', 'leilaoId': leilaoId, 
        'erro': 'not yet implemented', 'payload': payload}
    return jsonify(content)

# Connect to db
def db_conn():
    db = psycopg2.connect(user='', password='', port='5432', database='')
    return db

########
# Main #
########
if __name__ == '__main__':
    # Logger setup
    logging.basicConfig(filename="logs/test_log.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Logger formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    app.run(host='0.0.0.0', debug=True, threaded=True)