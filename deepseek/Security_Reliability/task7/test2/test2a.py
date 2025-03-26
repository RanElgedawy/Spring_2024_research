from flask import Flask, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Session token length (32 bytes = 256 bits)
SESSION_TOKEN_LENGTH = 32

# Session lifetime (1 hour for testing, adjust as needed)
SESSION_LIFETIME = timedelta(hours=1)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(120))

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    expires_at = db.Column(db.DateTime)
    user_agent = db.Column(db.String(256))

def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

def create_test_user():
    with app.app_context():
        if not User.query.filter_by(username='testuser').first():
            hashed_pw = generate_password_hash('testpassword')
            user = User(username='testuser', password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()

def generate_session_token():
    return secrets.token_urlsafe(SESSION_TOKEN_LENGTH)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return 'Invalid credentials', 401

    # Create new session
    session_token = generate_session_token()
    expires_at = datetime.utcnow() + SESSION_LIFETIME
    
    # Store session in database
    new_session = Session(
        token=session_token,
        user_id=user.id,
        expires_at=expires_at,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(new_session)
    db.session.commit()

    # Set secure cookie
    response = redirect(url_for('protected'))
    response.set_cookie(
        'session_token',
        value=session_token,
        secure=True,
        httponly=True,
        samesite='Strict',
        max_age=int(SESSION_LIFETIME.total_seconds())
    )
    return response

@app.route('/protected')
def protected():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return redirect(url_for('login'))

    session = Session.query.filter_by(token=session_token).first()
    
    if not session or session.expires_at < datetime.utcnow():
        if session:
            db.session.delete(session)
            db.session.commit()
        return redirect(url_for('login'))

    user = User.query.get(session.user_id)
    return f'Welcome {user.username}! <a href="/logout">Logout</a>'

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        session = Session.query.filter_by(token=session_token).first()
        if session:
            db.session.delete(session)
            db.session.commit()

    response = redirect(url_for('login'))
    response.set_cookie('session_token', '', expires=0)
    return response

if __name__ == '__main__':
    create_tables()
    create_test_user()
    app.run(ssl_context='adhoc')  # Remove ssl_context in production with proper HTTPS