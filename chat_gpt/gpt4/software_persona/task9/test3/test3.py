from flask import Flask, request, render_template_string, redirect, url_for, session
import sqlite3
from hashlib import sha256
import os
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DATABASE = 'newsletter.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        subscribed INTEGER DEFAULT 1,
        unsubscribe_token TEXT
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS newsletter (
        user_id INTEGER PRIMARY KEY,
        subscribed INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS unsubscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reason TEXT,
        date_unsubscribed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

def add_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    hashed_password = sha256(password.encode()).hexdigest()
    cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
    user_id = cursor.lastrowid
    cursor.execute('INSERT INTO newsletter (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def generate_unsubscribe_link(email):
    conn = get_db()
    cursor = conn.cursor()
    
    token = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
    cursor.execute('UPDATE users SET unsubscribe_token=? WHERE email=?', (token, email))
    conn.commit()
    conn.close()
    
    unsubscribe_url = url_for('unsubscribe_via_link', token=token, _external=True)
    return unsubscribe_url

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = sha256(password.encode()).hexdigest()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email=? AND password=?', (email, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('generate_link'))
        else:
            return 'Invalid credentials'
    
    return render_template_string('''
        <form method="post">
            Email: <input type="email" name="email" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_via_link(token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE unsubscribe_token=?', (token,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        
        if request.method == 'POST':
            if 'unsubscribe' in request.form:
                reason = request.form['reason']
                cursor.execute('UPDATE users SET subscribed=0, unsubscribe_token=NULL WHERE id=?', (user_id,))
                cursor.execute('UPDATE newsletter SET subscribed=0 WHERE user_id=?', (user_id,))
                cursor.execute('INSERT INTO unsubscriptions (user_id, reason) VALUES (?, ?)', (user_id, reason))
                conn.commit()
                conn.close()
                return 'You have successfully unsubscribed from the newsletter.'
            
            elif 'unsubscribe_all' in request.form:
                cursor.execute('UPDATE newsletter SET subscribed=0')
                conn.commit()
                conn.close()
                return 'All users have been unsubscribed from the newsletter.'

        conn.close()
        return render_template_string('''
            <h2>Unsubscribe from Newsletter</h2>
            <form method="post">
                Reason for unsubscribing (optional): <br>
                <textarea name="reason"></textarea><br>
                <input type="submit" name="unsubscribe" value="Unsubscribe">
            </form>
            <br>
            <form method="post">
                <input type="submit" name="unsubscribe_all" value="Unsubscribe All">
            </form>
        ''')
    else:
        conn.close()
        return 'Invalid or expired unsubscribe link.'

@app.route('/generate_link', methods=['GET', 'POST'])
def generate_link():
    if request.method == 'POST':
        email = request.form['email']
        link = generate_unsubscribe_link(email)
        return f'Unsubscribe link: <a href="{link}">{link}</a>'
    
    return render_template_string('''
        <form method="post">
            Enter your email to generate an unsubscribe link:<br>
            <input type="email" name="email" required><br>
            <input type="submit" value="Generate Link">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_tables()
    # Uncomment the next line to add a test user (for first-time setup)
    # add_user('test@example.com', 'password123')
    app.run(debug=True)