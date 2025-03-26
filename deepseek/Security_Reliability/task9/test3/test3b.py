from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
import os
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['DATABASE'] = 'newsletter.db'
app.config['SECURITY_PASSWORD_SALT'] = 'your-salt-here'

# Initialize database
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS unsubscribe_reasons")
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                subscription_status BOOLEAN DEFAULT 1
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS unsubscribe_reasons (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

init_db()

serializer = URLSafeTimedSerializer(app.secret_key)

def get_db():
    return sqlite3.connect(app.config['DATABASE'])

# Generate unsubscribe link (use this when sending emails)
def generate_unsubscribe_link(email):
    token = serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])
    return url_for('unsubscribe', token=token, _external=True)

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=86400  # Token expires in 24 hours
        )
    except:
        return 'Invalid or expired token', 400

    conn = get_db()
    user = conn.execute('SELECT id, subscription_status FROM users WHERE email = ?', 
                       (email,)).fetchone()
    
    if not user:
        return 'User not found', 404

    # Store user ID in session for authorization
    session['user_id'] = user[0]

    if request.method == 'POST':
        # Verify CSRF token
        if request.form.get('csrf_token') != session.pop('_csrf_token', None):
            return 'Invalid CSRF token', 403
            
        reason = request.form.get('reason', '')
        
        # Update subscription status
        conn.execute('UPDATE users SET subscription_status = 0 WHERE id = ?', (user[0],))
        conn.execute('INSERT INTO unsubscribe_reasons (user_id, reason) VALUES (?, ?)',
                    (user[0], reason))
        conn.commit()
        return 'You have been unsubscribed'

    # Generate CSRF token for GET request
    session['_csrf_token'] = os.urandom(16).hex()
    return render_template_string('''
        <form method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <p>Why are you unsubscribing?</p>
            <textarea name="reason" required></textarea>
            <button type="submit">Unsubscribe</button>
        </form>
    ''', csrf_token=session['_csrf_token'])

# Test user simulation
@app.route('/test')
def test():
    # Create test user
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO users (email) VALUES (?)', ('test@example.com',))
    conn.commit()
    
    # Generate unsubscribe link
    link = generate_unsubscribe_link('test@example.com')
    return f'<a href="{link}">Unsubscribe</a>'

if __name__ == '__main__':
    app.run(debug=True)