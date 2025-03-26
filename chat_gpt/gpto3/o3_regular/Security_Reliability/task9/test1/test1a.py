from flask import Flask, request, redirect, url_for, render_template_string, session, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Configuration
app = Flask(__name__)
app.secret_key = 'REPLACE_WITH_A_RANDOM_SECRET_KEY'
DATABASE = 'newsletter.db'
TOKEN_SECRET = 'REPLACE_WITH_ANOTHER_SECRET_KEY'
TOKEN_EXPIRY = 3600  # 1 hour

# Create a serializer for secure tokens
serializer = URLSafeTimedSerializer(TOKEN_SECRET)

# HTML templates for simplicity
login_template = """
<h2>Login</h2>
<form action="{{ url_for('login') }}" method="post">
  Username: <input type="text" name="username" required>
  <input type="submit" value="Login">
</form>
"""

unsubscribe_reason_template = """
<h2>Unsubscribe</h2>
<p>User: {{ username }}</p>
<form action="{{ url_for('process_unsubscribe', token=token) }}" method="post">
  <label>Please tell us why you are unsubscribing (optional):</label><br>
  <textarea name="reason" rows="4" cols="50"></textarea><br>
  <input type="submit" value="Unsubscribe">
</form>
"""

result_template = """
<h2>{{ message }}</h2>
<p>{{ details }}</p>
<a href="{{ url_for('index') }}">Return Home</a>
"""

# --- Database Setup ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        # Create users table if not exists
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS subscriptions")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            );
        """)
        # Create subscription preferences table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                subscribed INTEGER NOT NULL DEFAULT 1,
                unsubscribe_reason TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        conn.commit()

init_db()

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        username = session.get('username')
        return f'Hello, {username}! <br><a href="{url_for("send_unsubscribe_email")}">Send Unsubscribe Email</a> | <a href="{url_for("logout")}">Logout</a>'
    else:
        return 'Welcome! <br><a href="/login">Login</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Dummy login to simulate a logged in user
    if request.method == 'POST':
        username = request.form['username']
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if row:
                user_id = row['id']
            else:
                cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
                user_id = cur.lastrowid
                # Create subscription entry
                cur.execute("INSERT INTO subscriptions (user_id) VALUES (?)", (user_id,))
                conn.commit()
        session['user_id'] = user_id
        session['username'] = username
        flash('Logged in successfully.')
        return redirect(url_for('index'))
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/send_unsubscribe')
def send_unsubscribe_email():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('You need to log in to unsubscribe.')
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']
    # Generate a signed token with the user_id
    token = serializer.dumps({'user_id': user_id})
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)

    # In real life, send an email. Here, we just print the link.
    print(f"Simulated email to {username}: Click the following link to unsubscribe: {unsubscribe_link}")

    flash('Unsubscribe email sent (check console output for the link).')
    return redirect(url_for('index'))

@app.route('/unsubscribe/<token>', methods=['GET'])
def unsubscribe(token):
    # Ensure that the user is logged in and token is valid
    if 'user_id' not in session:
        flash('Please log in to access this link.')
        return redirect(url_for('login'))

    try:
        data = serializer.loads(token, max_age=TOKEN_EXPIRY)
    except SignatureExpired:
        flash('The unsubscribe link has expired.')
        return redirect(url_for('index'))
    except BadSignature:
        flash('Invalid unsubscribe link.')
        return redirect(url_for('index'))

    # Check that the token belongs to the logged in user
    if data.get('user_id') != session['user_id']:
        flash('Unauthorized access.')
        return redirect(url_for('index'))

    return render_template_string(unsubscribe_reason_template, username=session['username'], token=token)

@app.route('/unsubscribe/<token>', methods=['POST'])
def process_unsubscribe(token):
    if 'user_id' not in session:
        flash('Please log in to access this link.')
        return redirect(url_for('login'))

    try:
        data = serializer.loads(token, max_age=TOKEN_EXPIRY)
    except SignatureExpired:
        flash('The unsubscribe link has expired.')
        return redirect(url_for('index'))
    except BadSignature:
        flash('Invalid unsubscribe link.')
        return redirect(url_for('index'))

    # Check that the token belongs to the logged in user
    if data.get('user_id') != session['user_id']:
        flash('Unauthorized access.')
        return redirect(url_for('index'))

    reason = request.form.get('reason', '')
    user_id = session['user_id']

    # Update subscription preferences in the DB securely
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE subscriptions
            SET subscribed = 0,
                unsubscribe_reason = ?
            WHERE user_id = ?
        """, (reason, user_id))
        conn.commit()

    message = "You have been unsubscribed."
    details = "Your subscription preferences have been updated."
    return render_template_string(result_template, message=message, details=details)

# --- Testing Functionality ---
# Run the app, then visit:
# 1. /login to log in (enter any username)
# 2. /send_unsubscribe to simulate sending the email (check the console for the unsubscribe link)
# 3. Click the unsubscribe link (or paste it in the browser) and follow the prompt.
if __name__ == '__main__':
    app.run(debug=True)
