from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
import os
from itsdangerous import URLSafeSerializer, BadSignature

# Flask setup
app = Flask(__name__)
app.secret_key = 'a-very-secret-key'  # change this for production

# Token serializer for secure unsubscribe links
serializer = URLSafeSerializer(app.secret_key)

# Database filename
DB_FILE = 'app.db'

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS users")

        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT,
                subscribed INTEGER DEFAULT 1,
                unsubscribe_reason TEXT
            )
        ''')
        # Insert a test user if not exists
        c.execute("SELECT * FROM users WHERE email = ?", ('test@example.com',))
        if c.fetchone() is None:
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", ('test@example.com', 'password'))
        conn.commit()

init_db()

# Helper function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Route: Home
@app.route('/')
def home():
    user = session.get('user')
    return render_template_string('''
        <h1>Welcome{{ ' ' + user if user else '' }}!</h1>
        {% if user %}
            <p><a href="{{ url_for('send_unsubscribe') }}">Send unsubscribe email</a></p>
            <p><a href="{{ url_for('logout') }}">Logout</a></p>
        {% else %}
            <p><a href="{{ url_for('login') }}">Login as test user</a></p>
        {% endif %}
    ''', user=session.get('user'))

# Route: Login (for testing)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
            if user:
                session['user'] = user['email']
                session['user_id'] = user['id']
                flash('Logged in successfully!', 'info')
                return redirect(url_for('home'))
        flash('Invalid credentials', 'error')
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Email: <input type="text" name="email" value="test@example.com"><br>
            Password: <input type="password" name="password" value="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('home'))

# Route: Send unsubscribe email (simulated)
@app.route('/send_unsubscribe')
def send_unsubscribe():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'error')
        return redirect(url_for('login'))
    
    # Generate a token that includes the user ID (to be used in the unsubscribe URL)
    token = serializer.dumps({'user_id': session['user_id']})
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    
    # In a real system, you would email the unsubscribe_url to the user.
    # For testing, we print the link.
    flash(f"Unsubscribe link (simulate email): {unsubscribe_url}", 'info')
    return redirect(url_for('home'))

# Route: Unsubscribe process
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    try:
        data = serializer.loads(token)
        token_user_id = data.get('user_id')
    except BadSignature:
        flash('Invalid or tampered token.', 'error')
        return redirect(url_for('home'))
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to confirm unsubscription.', 'error')
        return redirect(url_for('login'))
    
    # Ensure that the token belongs to the logged in user
    if session['user_id'] != token_user_id:
        flash('You are not authorized to unsubscribe this account.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        # Update subscription status and record unsubscribe reason
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE id = ?", (reason, token_user_id))
            conn.commit()
        flash('You have been unsubscribed. Thank you for your feedback!', 'info')
        return redirect(url_for('home'))
    
    # Render form asking for unsubscribe reason
    return render_template_string('''
        <h2>Unsubscribe</h2>
        <p>Please let us know why you are unsubscribing (optional):</p>
        <form method="POST">
            <textarea name="reason" rows="4" cols="50"></textarea><br>
            <input type="submit" value="Unsubscribe">
        </form>
    ''')

if __name__ == '__main__':
    # Run the app for testing
    app.run(debug=True)
