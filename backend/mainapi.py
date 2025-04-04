from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS, cross_origin
from datetime import datetime
import hashlib

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"], methods=["GET", "OPTIONS"])
app.secret_key = 'supersecretkey'

# ---- LOGIN API (Basic Auth with SHA-256) ----
masterPassword = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # 'password'
masterUsername = 'username'

@app.route('/authenticatedroute', methods=['GET', 'OPTIONS'])
@cross_origin(origins="*", supports_credentials=True)
def auth_test():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    if request.authorization:
        encoded = request.authorization.password.encode()
        hasedResult = hashlib.sha256(encoded)
        if request.authorization.username == masterUsername and hasedResult.hexdigest() == masterPassword:
            return '<h1> Authorized user access </h1>'
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# ---- CLIENT API ----
clients = []

@app.route('/api/clients', methods=['GET'])
def get_clients():
    return jsonify(clients)

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.get_json()
    clients.append(data)
    return jsonify({'message': 'Client added successfully'})

# ---- BOOKING API ----
bookings = []

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    return jsonify(bookings)

@app.route('/api/bookings', methods=['POST'])
def add_booking():
    data = request.get_json()
    bookings.append(data)
    return jsonify({'message': 'Booking added successfully'})

# ---- DATETIME API ----
@app.route('/api/datetime/now', methods=['GET'])
def get_current_datetime():
    now = datetime.now()
    return jsonify({
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S')
    })

if __name__ == '__main__':
    app.run(debug=True, port=5050)