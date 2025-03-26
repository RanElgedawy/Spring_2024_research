from flask import Flask, request, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer, BadSignature
import os
import hashlib
import time

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.db'  # Change to MySQL if needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Secret key for signing cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript access
app.config['SESSION_COOKIE_SECURE'] = True  # Only allow cookies over HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Prevent CSRF
app.config['SESSION_COOKIE_DOMAIN'] = 'example.com'  # Restrict to your domain

db = SQLAlchemy(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Session table to manage sessions
class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    session_token = db.Column(db.String(256), nullable=False, unique=True)
    expires_at = db.Column(db.Integer, nullable=False)

# Auto-create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Generate a secure session token
def generate_session_token(user_id):
    token = serializer.dumps({'user_id': user_id})
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token_hash, token

# Verify a session token
def verify_session_token(token):
    try:
        data = serializer.loads(token, max_age=3600)  # Token expires in 1 hour
        return data['user_id']
    except BadSignature:
        return None

# Set the session cookie
def set_session_cookie(response, token):
    response.set_cookie(
        'session_token',
        token,
        httponly=True,
        secure=True,
        samesite='Strict',
        domain='localhost',  # Your domain here
        path='/'
    )

# Login route
@app.route('/login', methods=['POST'])
def login():
    user_id = request.json.get('user_id')  # Simulating authentication
    if user_id:
        token_hash, token = generate_session_token(user_id)
        expires_at = int(time.time()) + 3600  # Session valid for 1 hour
        
        # Save session in DB
        new_session = UserSession(user_id=user_id, session_token=token_hash, expires_at=expires_at)
        db.session.add(new_session)
        db.session.commit()

        response = make_response(jsonify({'message': 'Login successful'}))
        set_session_cookie(response, token)
        return response
    return jsonify({'error': 'Invalid credentials'}), 401

# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    token = request.cookies.get('session_token')
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session_to_delete = UserSession.query.filter_by(session_token=token_hash).first()
        if session_to_delete:
            db.session.delete(session_to_delete)
            db.session.commit()

        response = make_response(jsonify({'message': 'Logout successful'}))
        response.delete_cookie('session_token', domain='example.com', path='/')
        return response
    return jsonify({'error': 'No active session'}), 401

# Protected route
@app.route('/profile', methods=['GET'])
def profile():
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user_session = UserSession.query.filter_by(session_token=token_hash).first()

    if user_session and user_session.expires_at > time.time():
        return jsonify({'message': f'Hello, user {user_session.user_id}'})
    
    return jsonify({'error': 'Session expired or invalid'}), 401

# Test endpoint for functionality
@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'App is working'})

if __name__ == '__main__':
    app.run(debug=True)