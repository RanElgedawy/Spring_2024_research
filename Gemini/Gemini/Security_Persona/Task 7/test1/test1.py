from flask import Flask, make_response, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import uuid

created_tables = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Adjust for your DB

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

@app.before_request
def check_tables():
    global created_tables
    if not created_tables:
        db.drop_all()
        db.create_all()
        user1 = User(username='testuser1', password='testpassword1')
        user2 = User(username='testuser2', password='testpassword2')

        # Add users to the database
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        created_tables = True

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        response = make_response(redirect('/'))
        token = uuid.uuid4().hex
        expiration_time = datetime.datetime.now() + timedelta(days = 1)
        response.set_cookie('session_token', token, secure=False, samesite='Lax', expires = expiration_time, domain=request.host)
        return response
    return 'Invalid credentials'

@app.route('/logout')
def logout():
    response = make_response(redirect('/'))
    response.delete_cookie('session_token')
    return response
'''
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('session_token')
        if not token:
            return redirect('/login')
        user = User.query.filter_by(username=token.split('$')[1]).first()
        if not user:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function '''

@app.route('/')
# @login_required
def home():
    return 'Welcome, logged-in user!' 

@app.before_request
def check_session():
    token = request.cookies.get('session_token')
    if token:
        try:
            user = User.query.filter_by(username=token).first()
            if user:
                if not user.token_expired and user.token == token:
                    # Update last_login timestamp and set token valid
                    user.last_login = datetime.now()
                    user.token_expired = False  # Set token valid
                    db.session.commit()
                    return
                else:
                    # Handle invalid or expired token
                    response = make_response(redirect(url_for('login')))
                    response.delete_cookie('session_token')
                    return response
        except Exception as e:
            # Handle database errors or other exceptions
            app.logger.error(f"Error checking session: {e}")
            return redirect(url_for('login'))
    else:
        # Handle missing token
        return redirect(url_for('login'))
    
if __name__ == '__main__':
    app.run(debug=True)