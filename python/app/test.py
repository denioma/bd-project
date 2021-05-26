from flask import Flask, jsonify, request
import logging, time, psycopg2

app = Flask(__name__)

@app.route('/')
def landing():
    return 'Welcome to the Auction House!'

@app.route("/dbproj/user", methods=['POST'])
def register():
    payload = request.get_json()
    if payload["username"] is None or payload["password"] is None or payload["email"] is None:
        return "username, email and password required in request body"
    

# @app.route('/dbproj/user', methods=['PUT'])
# def auth():
#     payload = request.get_json()

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