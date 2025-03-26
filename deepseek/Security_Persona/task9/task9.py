from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import secrets
from datetime import datetime
import uuid
from datetime import timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DATABASE = 'newsletter.db'

# Enhanced database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS admin_actions")    
    c.execute("DROP TABLE IF EXISTS unsubscribe_tokens")  # Add this
    
    # Add unsubscribe_tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS unsubscribe_tokens
                 (token TEXT PRIMARY KEY,
                  user_id TEXT,
                  expires_at DATETIME,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, 
                  email TEXT UNIQUE, 
                  is_subscribed INTEGER DEFAULT 1,
                  is_admin INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admin_actions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  admin_id TEXT,
                  action TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(admin_id) REFERENCES users(id))''')
    
    # Create initial admin user if none exists
    c.execute('''INSERT OR IGNORE INTO users (id, email, is_admin) 
                 VALUES (?, ?, ?)''',
              (str(uuid.uuid4()), 'admin@example.com', 1))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Security helper functions
def generate_token():
    return secrets.token_urlsafe(32)

# Admin authorization decorator
def admin_required(f):
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return "Administrator privileges required", 403
        return f(*args, **kwargs)
    return decorated

# Routes

@app.route('/')
def index():
    return "Home Page"

@app.route('/send_unsubscribe_email', methods=['GET'])
def send_unsubscribe_email():
    # Test route to simulate sending unsubscribe email
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Generate unsubscribe token
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=24)
    
    # Store token in database
    c.execute('INSERT INTO unsubscribe_tokens (token, user_id, expires_at) VALUES (?, ?, ?)',
              (token, session['user_id'], expires_at))
    
    # In real implementation, send email with unsubscribe link
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    print(f"Unsubscribe link: {unsubscribe_url}")  # For testing purposes
    
    conn.commit()
    conn.close()
    return "Unsubscribe email sent (check console for link)"

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    token = request.args.get('token')
    conn = get_db()
    c = conn.cursor()
    
    # Verify token validity
    c.execute('SELECT * FROM unsubscribe_tokens WHERE token = ? AND expires_at > ?',
             (token, datetime.now()))
    token_data = c.fetchone()
    
    if not token_data:
        conn.close()
        return "Invalid or expired token", 400
    
    if request.method == 'POST':
        # Process unsubscribe
        try:
            c.execute('UPDATE users SET is_subscribed = 0 WHERE id = ?',
                     (token_data['user_id'],))
            c.execute('DELETE FROM unsubscribe_tokens WHERE token = ?', (token,))
            conn.commit()
            return "Unsubscribed successfully"
        except sqlite3.Error as e:
            conn.rollback()
            return "Database error", 500
        finally:
            conn.close()
    
    return render_template('unsubscribe_form.html')

# Admin panel route
@app.route('/admin', endpoint='admin_panel', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    conn = get_db()
    
    if request.method == 'POST':
        # Handle mass unsubscribe
        if request.form.get('action') == 'unsubscribe_all':
            try:
                c = conn.cursor()
                # Update all users' subscription status
                c.execute('UPDATE users SET is_subscribed = 0')
                # Log admin action
                c.execute('''INSERT INTO admin_actions 
                             (admin_id, action) VALUES (?, ?)''',
                          (session['user_id'], 'MASS_UNSUBSCRIBE'))
                conn.commit()
                flash_message = "All users have been unsubscribed"
            except sqlite3.Error as e:
                conn.rollback()
                flash_message = f"Error: {str(e)}"
            finally:
                conn.close()
            return render_template('admin.html', flash_message=flash_message)
    
    # Get statistics for display
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE is_subscribed = 1')
    subscribed_users = c.fetchone()[0]
    
    c.execute('''SELECT * FROM admin_actions 
                 ORDER BY timestamp DESC LIMIT 10''')
    recent_actions = c.fetchall()
    
    conn.close()
    
    return render_template('admin.html',
                         total_users=total_users,
                         subscribed_users=subscribed_users,
                         recent_actions=recent_actions)

# Updated login handling
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, is_admin FROM users WHERE email = ?''', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['is_admin'] = bool(user['is_admin'])
        return redirect(url_for('admin_panel' if user['is_admin'] else 'index'))
    return "Invalid credentials", 401

# Security enhancements
@app.before_request
def check_admin_access():
    if request.path.startswith('/admin') and not session.get('is_admin'):
        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)