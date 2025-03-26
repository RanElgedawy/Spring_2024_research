import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, make_response, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///sessions.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SESSION_COOKIE_NAME': 'secure_session',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': True,  # Set to True in production (HTTPS only)
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_DOMAIN': os.environ.get('DOMAIN', 'localhost'),
    'PERMANENT_SESSION_LIFETIME': timedelta(minutes=30)
})

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token_hash = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    user_agent = db.Column(db.String(255))
    
    __table_args__ = (db.Index('ix_session_token_hash', 'session_token_hash'),)

# Create tables if they don't exist
with app.app_context():
    db.drop_all()
    db.create_all()

def create_test_user():
    with app.app_context():
        test_user = User(
            email='test@example.com',
            password_hash=bcrypt.hashpw('securepassword'.encode(), bcrypt.gensalt()).decode()
        )
        db.session.add(test_user)
        db.session.commit()
        
def create_session(user_id, user_agent):
    # Generate secure random token
    token = secrets.token_urlsafe(64)
    token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()
    
    # Set session expiration
    expires_at = datetime.utcnow() + app.config['PERMANENT_SESSION_LIFETIME']
    
    # Store hashed token in database
    session = Session(
        user_id=user_id,
        session_token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent
    )
    db.session.add(session)
    db.session.commit()
    
    return token

def validate_session(token, user_agent):
    if not token:
        return None
    
    # Find session by token hash
    token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt())
    session = Session.query.filter(
        Session.session_token_hash == token_hash.decode(),
        Session.expires_at > datetime.utcnow()
    ).first()
    
    if not session or session.user_agent != user_agent:
        return None
    
    return session.user_id

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Validate user credentials (pseudo-code)
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        abort(401)
    
    # Create new session
    session_token = create_session(user.id, request.headers.get('User-Agent', ''))
    
    # Set secure cookie
    resp = make_response(redirect(url_for('dashboard')))
    resp.set_cookie(
        key=app.config['SESSION_COOKIE_NAME'],
        value=session_token,
        expires=datetime.utcnow() + app.config['PERMANENT_SESSION_LIFETIME'],
        httponly=app.config['SESSION_COOKIE_HTTPONLY'],
        secure=app.config['SESSION_COOKIE_SECURE'],
        samesite=app.config['SESSION_COOKIE_SAMESITE'],
        domain=app.config['SESSION_COOKIE_DOMAIN']
    )
    return resp

@app.route('/logout')
def logout():
    token = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
    if token:
        token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()
        Session.query.filter_by(session_token_hash=token_hash).delete()
        db.session.commit()
    
    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie(app.config['SESSION_COOKIE_NAME'])
    return resp

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
    user_id = validate_session(token, request.headers.get('User-Agent', ''))
    
    if not user_id:
        abort(401)
    
    return f"Welcome to your dashboard! User ID: {user_id}"

# Test routes
@app.route('/test-login')
def test_login():
    return '''
    <form method="post" action="/login">
        <input type="email" name="email" placeholder="Email" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
    '''

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # adhoc SSL for testing