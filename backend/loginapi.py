import hashlib
from flask import Flask, request, make_response
from flask_cors import CORS

app = Flask(__name__)
app.config["DEBUG"] = True

# Allow Authorization header & OPTIONS requests
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"], methods=["GET", "OPTIONS"])

masterPassword = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
masterUsername = 'username'

@app.route('/authenticatedroute', methods=['GET', 'OPTIONS'])
def auth_test():
    if request.method == 'OPTIONS':
        # Preflight request successful
        return make_response('', 200)

    if request.authorization:
        encoded = request.authorization.password.encode()
        hasedResult = hashlib.sha256(encoded)
        if request.authorization.username == masterUsername and hasedResult.hexdigest() == masterPassword:
            return '<h1> Authorized user access </h1>'
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

if __name__ == '__main__':
    app.run(port=5050)
