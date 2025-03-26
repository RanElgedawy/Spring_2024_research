from flask import Flask, request, redirect, url_for, render_template, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to something unique and secret
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set the session cookie to expire after a certain amount of time
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)  # Set session lifetime to 30 minutes

# Set the session cookie to be valid only for the current domain, not subdomains
app.config['SESSION_COOKIE_DOMAIN'] = None  # None means the cookie is only valid for the current domain, not subdomains

db = SQLAlchemy(app)

def initialize_database():
    """Initialize the database and create tables if they don't exist."""
    with app.app_context():
        db.create_all()

# Home route (for testing)
@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id'], session_token=session.get('session_token')).first()
        if user:
            return f'Logged in as {user.username}'
    return 'You are not logged in'

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # Generate a new session token and update the user's session
            new_session_token = str(uuid.uuid4())
            user.session_token = new_session_token
            db.session.commit()

            # Set the session information
            session['user_id'] = user.id
            session['session_token'] = new_session_token
            session.permanent = True  # Session will persist with the defined lifetime

            return redirect(url_for('home'))
        return 'Invalid credentials'
    return render_template('login.html')

# Route for handling logout
@app.route('/logout')
def logout():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        if user:
            user.session_token = None  # Invalidate the current session token
            db.session.commit()
    session.pop('user_id', None)
    session.pop('session_token', None)
    return redirect(url_for('home'))

# Function to protect routes
@app.before_request
def load_logged_in_user():
    initialize_database()  # Ensure the database is initialized before each request
    user_id = session.get('user_id')
    session_token = session.get('session_token')
    if user_id and session_token:
        g.user = User.query.filter_by(id=user_id, session_token=session_token).first()
        if g.user is None:
            # Invalidate the session if the token doesn't match
            session.pop('user_id', None)
            session.pop('session_token', None)
    else:
        g.user = None

# User model for storing user data
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    session_token = db.Column(db.String(120), unique=True, nullable=True)

# Add a test user (for testing purposes)
@app.route('/create_user')
def create_user():
    initialize_database()  # Ensure the database is initialized
    username = "testuser"
    password = generate_password_hash("testpassword")
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return 'Test user created'

if __name__ == '__main__':
    initialize_database()  # Initialize the database when the app starts
    app.run(debug=True)