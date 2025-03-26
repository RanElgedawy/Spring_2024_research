from flask import Flask, request, jsonify, make_response, url_for
import secrets
import hashlib
import time
from urllib.parse import urlparse

app = Flask(__name__)

# Get the current domain dynamically
def get_current_domain(request):
    parsed_url = urlparse(request.url_root)
    domain = parsed_url.netloc
    if '.' in domain:
        # Exclude subdomains that require authentication
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            domain = '.'.join(domain_parts[1:])
    return domain

# Simulated user database
users = {
    "user1": {"password": "password1", "email": "user1@example.com"}
}

# Session data stored in memory (In production, consider using a more persistent storage like Redis)
sessions = {}

# Function to generate a secure session token
def generate_session_token():
    return secrets.token_hex(32)

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to check if session token is expired
def is_session_expired(session_token):
    if session_token in sessions:
        expiration_time = sessions[session_token]['expiration_time']
        return time.time() > expiration_time
    return True

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in users and hash_password(password) == hash_password(users[username]['password']):
        # Invalidate previous session if exists
        for token, session in sessions.items():
            if session['username'] == username:
                del sessions[token]
                break
        
        session_token = generate_session_token()
        sessions[session_token] = {
            'username': username,
            'expiration_time': time.time() + (60 * 60)  # Expiration time set to 1 hour from now
        }
        response = make_response(jsonify({'message': 'Login successful', 'session_token': session_token}))
        response.set_cookie('session_token', session_token, domain=get_current_domain(request), secure=True, httponly=True, samesite='Strict')
        return response, 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# Route to check if a user is logged in
@app.route('/check_login', methods=['GET'])
def check_login():
    session_token = request.cookies.get('session_token')
    if session_token in sessions and not is_session_expired(session_token):
        return jsonify({'logged_in': True, 'username': sessions[session_token]['username'], 'session_token': session_token})
    else:
        return jsonify({'logged_in': False})

# Route for user logout
@app.route('/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')
    if session_token in sessions:
        del sessions[session_token]
    response = make_response(jsonify({'message': 'Logout successful'}))
    response.set_cookie('session_token', '', expires=0, domain=get_current_domain(request))
    return response, 200

if __name__ == '__main__':
    app.run(debug=True)