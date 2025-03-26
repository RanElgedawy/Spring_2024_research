from flask import Flask, request, redirect, url_for, render_template, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import uuid
import hashlib
import hmac

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this for security
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    session_token = db.Column(db.String(128), nullable=True)

# Helper function to create HMAC token
def create_token(user_id):
    token = str(uuid.uuid4())
    token_hash = hmac.new(app.secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()
    return token, token_hash

# Route to initialize database
@app.route('/initdb')
def init_db():
    db.drop_all()
    db.create_all()
    return 'Database Initialized!'

# Route for user registration (for testing purposes)
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if User.query.filter_by(username=username).first():
        return 'User already exists!'
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    return 'User registered!'

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        # Create session token
        token, token_hash = create_token(user.id)
        user.session_token = token_hash
        db.session.commit()

        # Create secure cookie
        resp = make_response('Logged in!')
        resp.set_cookie(
            'session_id', token, 
            httponly=True, secure=True, samesite='Strict', 
            domain=request.host.split(':')[0]
        )
        return resp
    return 'Invalid credentials', 401

# Route to check if user is authenticated
@app.route('/dashboard')
def dashboard():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return 'Unauthorized', 401
    
    # Validate the session
    user = User.query.filter_by(session_token=hmac.new(app.secret_key.encode(), session_id.encode(), hashlib.sha256).hexdigest()).first()
    if not user:
        return 'Unauthorized', 401
    
    return f'Welcome, {user.username}!'

# Route to log out user
@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        # Invalidate session
        user = User.query.filter_by(session_token=hmac.new(app.secret_key.encode(), session_id.encode(), hashlib.sha256).hexdigest()).first()
        if user:
            user.session_token = None
            db.session.commit()
        
        # Clear the cookie
        resp = make_response(redirect(url_for('dashboard')))
        resp.delete_cookie('session_id', domain=request.host.split(':')[0])
        return resp
    return redirect(url_for('dashboard'))

# Test landing page
@app.route('/')
def index():
    return '''
        <h2>Login</h2>
        <form method="POST" action="/login">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
        <a href="/register">Register</a>
    '''

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Running with HTTPS for secure cookies