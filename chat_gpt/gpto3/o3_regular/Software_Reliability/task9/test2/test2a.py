from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

DATABASE = 'newsletter.db'

# HTML templates for simplicity
login_template = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:red;">
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="POST">
  Email: <input type="text" name="email" required><br>
  Password: <input type="password" name="password" required><br>
  <input type="submit" value="Login">
</form>
"""

unsubscribe_template = """
<!doctype html>
<title>Unsubscribe</title>
<h2>Unsubscribe from Newsletter</h2>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:green;">
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="POST">
  Optional Reason:<br>
  <textarea name="reason" rows="4" cols="50"></textarea><br>
  <input type="submit" value="Unsubscribe">
</form>
"""

status_template = """
<!doctype html>
<title>Status</title>
<h2>Subscription Status</h2>
<p>Email: {{ email }}</p>
<p>Subscribed: {{ subscribed }}</p>
{% if reason %}
<p>Unsubscribe Reason: {{ reason }}</p>
{% endif %}
{% if unsubscribed_at %}
<p>Unsubscribed At: {{ unsubscribed_at }}</p>
{% endif %}
"""

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Create a simple users table
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS newsletter_subscriptions")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create a newsletter subscription table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed INTEGER NOT NULL DEFAULT 1,
            reason TEXT,
            unsubscribed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def seed_db():
    """Insert a test user if not already present."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Use fixed credentials for testing
    test_email = 'test@example.com'
    test_password = 'password'
    try:
        cur.execute('INSERT INTO users (email, password) VALUES (?, ?)', (test_email, test_password))
        cur.execute('INSERT INTO newsletter_subscriptions (email, subscribed) VALUES (?, ?)', (test_email, 1))
        conn.commit()
    except sqlite3.IntegrityError:
        # User already exists
        pass
    finally:
        conn.close()

@app.before_first_request
def setup():
    init_db()
    seed_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    A simple login route for testing.
    Use email: test@example.com and password: password.
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_email'] = email
            flash('Logged in successfully.')
            return redirect(url_for('unsubscribe'))
        else:
            flash('Invalid credentials.')
    return render_template_string(login_template)

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """
    Route for unsubscribing from the newsletter.
    Verifies that the user is logged in, then updates the subscription status.
    """
    if 'user_email' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        unsubscribed_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        cur = conn.cursor()
        # Verify that the email exists in our subscription table
        cur.execute('SELECT * FROM newsletter_subscriptions WHERE email = ?', (user_email,))
        record = cur.fetchone()
        if record:
            cur.execute('''
                UPDATE newsletter_subscriptions 
                SET subscribed = 0, reason = ?, unsubscribed_at = ? 
                WHERE email = ?
            ''', (reason if reason else None, unsubscribed_at, user_email))
            conn.commit()
            flash('You have been unsubscribed.')
        else:
            flash('Subscription record not found.')
        conn.close()
        return redirect(url_for('status'))
    
    return render_template_string(unsubscribe_template)

@app.route('/status')
def status():
    """
    Route to check the current newsletter subscription status for the logged-in user.
    """
    if 'user_email' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    user_email = session['user_email']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM newsletter_subscriptions WHERE email = ?', (user_email,))
    record = cur.fetchone()
    conn.close()
    if record:
        return render_template_string(status_template,
                                      email=record['email'],
                                      subscribed=bool(record['subscribed']),
                                      reason=record['reason'],
                                      unsubscribed_at=record['unsubscribed_at'])
    else:
        flash('Subscription record not found.')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Remove the database file if you want a fresh start (for testing only)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    # Start the Flask app
    app.run(debug=True)
