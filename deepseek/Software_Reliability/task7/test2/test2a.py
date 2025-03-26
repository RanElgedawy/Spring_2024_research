from flask import Flask, request, redirect, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime
import os

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.urandom(24),
    SQLALCHEMY_DATABASE_URI='sqlite:///sessions.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_NAME='ecommerce_session',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,  # Should be True in production (HTTPS)
    SESSION_COOKIE_SAMESITE='Lax'
)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Session(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref='sessions')

# Create tables and test user
@app.before_first_request
def initialize_data():
    db.drop_all()
    db.create_all()
    
    # Create test user if none exists
    if not User.query.first():
        test_user = User(email='test@example.com')
        test_user.set_password('password')
        db.session.add(test_user)
        db.session.commit()

def create_session(user):
    # Remove existing sessions
    Session.query.filter_by(user_id=user.id).delete()
    
    # Create new session
    session_id = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=2)
    
    new_session = Session(
        id=session_id,
        user_id=user.id,
        expires_at=expires_at
    )
    
    db.session.add(new_session)
    db.session.commit()
    return session_id

def validate_session(session_id):
    if not session_id:
        return None
    
    session = Session.query.get(session_id)
    if not session or session.expires_at < datetime.datetime.now():
        return None
    
    return session.user

def session_required(f):
    def wrapper(*args, **kwargs):
        session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
        user = validate_session(session_id)
        
        if not user:
            return redirect('/login')
        
        return f(user, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session_id = create_session(user)
            response = redirect('/dashboard')
            response.set_cookie(
                key=app.config['SESSION_COOKIE_NAME'],
                value=session_id,
                expires=datetime.datetime.now() + datetime.timedelta(hours=2),
                domain=None,  # Current domain only
                secure=app.config['SESSION_COOKIE_SECURE'],
                httponly=app.config['SESSION_COOKIE_HTTPONLY'],
                samesite=app.config['SESSION_COOKIE_SAMESITE']
            )
            return response
        
        return 'Invalid credentials', 401
    
    # Login form for testing
    return '''
        <form method="post">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
    if session_id:
        Session.query.filter_by(id=session_id).delete()
        db.session.commit()
    
    response = redirect('/login')
    response.delete_cookie(app.config['SESSION_COOKIE_NAME'])
    return response

@app.route('/dashboard')
@session_required
def dashboard(user):
    return f'Welcome {user.email}! <a href="/logout">Logout</a>'

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)