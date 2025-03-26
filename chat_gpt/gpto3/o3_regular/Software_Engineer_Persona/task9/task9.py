from flask import Flask, request, session, redirect, url_for, render_template_string, g, flash
import sqlite3
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
DATABASE = 'newsletter.db'

def get_db():
    """Establish and return a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # allows column access by name
    return db

def init_db():
    """Create tables (if they don't exist) and insert a test user with a subscription record."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create newsletter subscriptions table with an unsubscribe_token column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                subscribed INTEGER NOT NULL,  -- 1 = subscribed, 0 = unsubscribed
                reason TEXT,
                updated_at TEXT,
                unsubscribe_token TEXT UNIQUE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Insert a test user if one doesn't exist
        cursor.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', ('test@example.com', 'password'))
            user_id = cursor.lastrowid
            token = secrets.token_urlsafe(16)
            cursor.execute('''
                INSERT INTO newsletter_subscriptions (user_id, email, subscribed, updated_at, unsubscribe_token)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, 'test@example.com', 1, datetime.now().isoformat(), token))
        db.commit()

def generate_unsubscribe_link(user_id):
    """
    Generate a unique unsubscribe link for the given user by retrieving the stored token.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT unsubscribe_token FROM newsletter_subscriptions WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        token = row['unsubscribe_token']
        return url_for('unsubscribe_with_token', token=token, _external=True)
    return None

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'user_id' in session:
        link = generate_unsubscribe_link(session['user_id'])
        return render_template_string('''
            <h2>Welcome, {{ email }}</h2>
            <p>
                <a href="{{ url_for('unsubscribe') }}">Unsubscribe (Logged In)</a>
                | <a href="{{ url_for('logout') }}">Logout</a>
            </p>
            <p>Your unique unsubscribe link: <a href="{{ link }}">{{ link }}</a></p>
            <hr>
            <!-- Unsubscribe All Button (e.g., an admin feature) -->
            <form method="post" action="{{ url_for('unsubscribe_all') }}">
                <input type="submit" value="Unsubscribe All">
            </form>
        ''', email=session.get('email'), link=link)
    return "You are not logged in. <a href='/login'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """A simple login page to simulate a logged-in session."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            flash("Logged in successfully!")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Email: <input type="text" name="email" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    """Clear the session to log out the user."""
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('index'))

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """
    Allows a logged-in user to unsubscribe from the newsletter.
    Verifies the user’s identity via session data and updates their subscription record.
    """
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM newsletter_subscriptions WHERE user_id = ?', (session['user_id'],))
    subscription = cursor.fetchone()

    if request.method == 'POST':
        reason = request.form.get('reason', '')
        user_email = session.get('email')
        if subscription and subscription['email'] != user_email:
            flash("User identity verification failed.")
            return redirect(url_for('unsubscribe'))
        
        now = datetime.now().isoformat()
        if subscription:
            cursor.execute('''
                UPDATE newsletter_subscriptions
                SET subscribed = ?, reason = ?, updated_at = ?
                WHERE user_id = ?
            ''', (0, reason, now, session['user_id']))
        else:
            token = secrets.token_urlsafe(16)
            cursor.execute('''
                INSERT INTO newsletter_subscriptions (user_id, email, subscribed, reason, updated_at, unsubscribe_token)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], user_email, 0, reason, now, token))
        db.commit()
        flash("You have successfully unsubscribed from the newsletter.")
        return redirect(url_for('index'))

    return render_template_string('''
        <h2>Unsubscribe from Newsletter (Logged In)</h2>
        <form method="post">
            <label for="reason">Optional reason for unsubscription:</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <p><a href="/">Go Back</a></p>
    ''')

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_with_token(token):
    """
    Allows a user to unsubscribe using their unique token (from the unsubscribe link).
    No login is required.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM newsletter_subscriptions WHERE unsubscribe_token = ?", (token,))
    subscription = cursor.fetchone()
    if not subscription:
        flash("Invalid unsubscribe link.")
        return redirect(url_for('index'))
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE newsletter_subscriptions
            SET subscribed = ?, reason = ?, updated_at = ?
            WHERE unsubscribe_token = ?
        ''', (0, reason, now, token))
        db.commit()
        flash("You have successfully unsubscribed from the newsletter using your unique link.")
        return redirect(url_for('index'))
    return render_template_string('''
        <h2>Unsubscribe from Newsletter (Unique Link)</h2>
        <p>Email: {{ email }}</p>
        <form method="post">
            <label for="reason">Optional reason for unsubscription:</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <p><a href="/">Go Back</a></p>
    ''', email=subscription['email'])

@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    """
    Called when the "Unsubscribe All" button is clicked.
    Updates the newsletter_subscriptions table by setting the subscribed
    field to 0 (false) for all users.
    """
    # Optionally, you may want to restrict this action (e.g., admin only).
    db = get_db()
    cursor = db.cursor()
    now = datetime.now().isoformat()
    cursor.execute("UPDATE newsletter_subscriptions SET subscribed = 0, updated_at = ?", (now,))
    db.commit()
    flash("All users have been unsubscribed from the newsletter.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
