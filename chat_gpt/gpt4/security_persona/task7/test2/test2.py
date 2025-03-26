from flask import Flask, request, redirect, url_for, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
import uuid

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    session_token = db.Column(db.String(200), unique=True, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # New column

# Create the database and the User table
with app.app_context():
    # db.drop_all()
    db.create_all()

# Route to register new users
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            return "User already exists"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Route to login users
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session_token = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # Session expires in 1 hour
            user.session_token = session_token
            user.expires_at = expires_at
            db.session.commit()

            # Debugging logs
            print(f"User {username} logged in with session token {session_token}")

            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie(
                'session_token',
                session_token,
                httponly=True,
                secure=False,
                samesite='Strict',
                domain='localhost',
                expires=expires_at  # Set the cookie to expire at the same time
            )
            return resp

        return "Invalid credentials"

    return render_template('login.html')

# Route to a protected dashboard
@app.route('/dashboard')
def dashboard():
    session_token = request.cookies.get('session_token')
    user = User.query.filter_by(session_token=session_token).first()

    if user:
        current_time = datetime.now(timezone.utc)  # Ensure the current time is timezone-aware
        expires_at = user.expires_at

        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at and expires_at > current_time:
            return f"Welcome {user.username} to your dashboard!"
        else:
            print("Session expired.")
            return redirect(url_for('logout'))
    else:
        print(f"Session token in request: {session_token}")
        print("No valid user found with session token.")
    
    return redirect(url_for('login'))

# Route to logout users
@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    user = User.query.filter_by(session_token=session_token).first()

    if user:
        user.session_token = None
        user.expires_at = None  # Clear the expiration time
        db.session.commit()

    resp = make_response(redirect(url_for('login')))
    resp.delete_cookie('session_token', domain='yourdomain.com')
    return resp

if __name__ == '__main__':
    app.run(debug=True)