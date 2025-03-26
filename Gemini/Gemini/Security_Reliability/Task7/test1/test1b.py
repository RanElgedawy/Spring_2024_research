import sqlite3
import jwt
import datetime
from flask import Flask, request, make_response, jsonify

def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')
    conn.commit()
    conn.close()

def generate_jwt(user_id):
    # Replace 'your_secret_key' with a strong secret key
    secret_key = 'your_secret_key'
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

def verify_jwt(token):
    try:
        # Replace 'your_secret_key' with the same secret key used for encoding
        payload = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password'] 

    # Validate credentials against the database
    # ...
    if credentials_are_valid:
        user_id = get_user_id(username)
        token = generate_jwt(user_id)
        resp = make_response(jsonify({'token': token}))
        resp.set_cookie('jwt', token, httponly=True, samesite='Lax')
        return resp

@app.route('/protected')
def protected():
    token = request.cookies.get('jwt')
    if token:
        user_id = verify_jwt(token)
        if user_id:
            return jsonify({'message': 'You are authorized'})
        else:
            return jsonify({'message': 'Invalid token'})
    else:
        return jsonify({'message': 'Token not found'})

if __name__ == '__main__':
    create_database()
    app.run(debug=True)