# app.py
import sqlite3
from datetime import datetime, timedelta, timezone
from flask import Flask, request, redirect, make_response, render_template
import bcrypt
import jwt

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
app.config['DATABASE'] = 'users.db'
app.config['JWT_EXPIRATION_DELTA'] = timedelta(minutes=15)

# Initialize database and create test user
def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute('SELECT id FROM users WHERE username = "testuser"')
    if cursor.fetchone() is None:
        hashed_password = bcrypt.hashpw('testpass'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      ('testuser', hashed_password))
    conn.commit()
    conn.close()

init_db()

# JWT Token handling
def generate_jwt(user_id):
    expiration = datetime.now(timezone.utc) + app.config['JWT_EXPIRATION_DELTA']
    payload = {
        'user_id': user_id,
        'exp': expiration,
        'iss': 'your-ecom-domain.com'
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_jwt(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], 
                           algorithms=['HS256'],
                           options={'require_exp': True, 'verify_iss': True},
                           issuer='your-ecom-domain.com')
        return payload['user_id']
    except jwt.InvalidTokenError:
        return None

# Authentication decorator
def login_required(view_func):
    def wrapped_view(**kwargs):
        token = request.cookies.get('session_token')
        if not token or not verify_jwt(token):
            return redirect('/login')
        return view_func(**kwargs)
    return wrapped_view

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password, user[1]):
            response = make_response(redirect('/dashboard'))
            response.set_cookie(
                'session_token',
                value=generate_jwt(user[0]),
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=int(app.config['JWT_EXPIRATION_DELTA'].total_seconds())
            return response
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout', methods=['POST'])
def logout():
    response = make_response(redirect('/login'))
    response.set_cookie('session_token', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Remove in production when behind HTTPS proxy