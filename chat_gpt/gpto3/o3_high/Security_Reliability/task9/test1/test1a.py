from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
import os
import hmac, hashlib, base64

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'  # Change this for production!
DATABASE = 'newsletter.db'
TOKEN_SECRET = 'another-secret-key'  # Used for token generation

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the users table (if it doesn't exist) and a test user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT, -- Plaintext for demo only; use hashing in production!
            subscribed INTEGER NOT NULL DEFAULT 1,
            unsubscribe_reason TEXT
        )
    ''')
    # Insert a test user if not already present
    cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "testpass"))
    conn.commit()
    conn.close()

def generate_token(user_id, secret_key):
    """Generate a token that encodes the user ID with an HMAC signature."""
    msg = str(user_id).encode()
    signature = hmac.new(secret_key.encode(), msg, hashlib.sha256).hexdigest()
    token = f"{user_id}:{signature}"
    token_bytes = token.encode()
    return base64.urlsafe_b64encode(token_bytes).decode()

def verify_token(token, secret_key):
    """Verify the token and return the user ID if valid."""
    try:
        token_bytes = base64.urlsafe_b64decode(token)
        token_str = token_bytes.decode()
        user_id_str, signature = token_str.split(":")
        expected_signature = hmac.new(secret_key.encode(), user_id_str.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature, expected_signature):
            return int(user_id_str)
    except Exception as e:
        print("Token verification failed:", e)
    return None

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

# Simple login route for testing
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            flash('Logged in successfully!', 'info')
            return redirect(url_for('profile'))
        else:
            flash('Invalid credentials', 'error')
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input type="text" name="username" /><br/>
            Password: <input type="password" name="password" /><br/>
            <input type="submit" value="Login" />
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return render_template_string('''
        <h2>Profile</h2>
        <p>Username: {{ user["username"] }}</p>
        <p>Subscribed: {{ "Yes" if user["subscribed"] else "No" }}</p>
        {% if not user["subscribed"] and user["unsubscribe_reason"] %}
            <p>Unsubscribe Reason: {{ user["unsubscribe_reason"] }}</p>
        {% endif %}
        <a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a><br/>
        <a href="{{ url_for('logout') }}">Logout</a>
    ''', user=user)

# Endpoint to simulate sending an unsubscribe email
@app.route('/send_unsubscribe_email')
def send_unsubscribe_email():
    if 'user_id' not in session:
        flash('You must be logged in to perform this action', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    token = generate_token(user_id, TOKEN_SECRET)
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    # Simulate email sending (in production, integrate with an email service)
    flash(f"Simulated email sent with unsubscribe link: {unsubscribe_link}", 'info')
    return redirect(url_for('profile'))

# Unsubscribe route: shows the reason form and updates subscription status upon submission
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'user_id' not in session:
        flash('You must be logged in to unsubscribe', 'error')
        return redirect(url_for('login'))
    
    token = request.args.get('token')
    if not token:
        flash('Invalid unsubscribe link', 'error')
        return redirect(url_for('profile'))
    
    token_user_id = verify_token(token, TOKEN_SECRET)
    if token_user_id is None or token_user_id != session['user_id']:
        flash('Unauthorized unsubscribe attempt', 'error')
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        conn = get_db_connection()
        conn.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE id = ?", (reason, session['user_id']))
        conn.commit()
        conn.close()
        flash('You have been unsubscribed from our newsletter.', 'info')
        return redirect(url_for('profile'))
    
    return render_template_string('''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="POST">
            <label>Please let us know why you are unsubscribing (optional):</label><br/>
            <textarea name="reason" rows="4" cols="50"></textarea><br/>
            <input type="submit" value="Unsubscribe" />
        </form>
    ''')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
