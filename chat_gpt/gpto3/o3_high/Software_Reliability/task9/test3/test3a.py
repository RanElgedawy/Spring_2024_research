from flask import Flask, request, render_template_string, session, redirect, url_for, flash
import sqlite3
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # In production, use a secure random key

DATABASE = 'newsletter.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Create a users table with newsletter subscription info
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            subscribed INTEGER NOT NULL DEFAULT 1,
            unsubscribe_reason TEXT,
            unsubscribe_date TEXT
        )
    ''')
    # Insert a dummy user for testing (if not already present)
    try:
        c.execute('INSERT INTO users (email, password) VALUES (?, ?)', ('test@example.com', 'password'))
    except sqlite3.IntegrityError:
        # User already exists
        pass
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Simple login route for testing purposes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchone()
        conn.close()
        if user:
            session['user_email'] = user['email']
            flash('Logged in successfully.')
            return redirect(url_for('unsubscribe'))
        else:
            flash('Invalid credentials.')
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Email: <input type="email" name="email" required /><br/>
            Password: <input type="password" name="password" required /><br/>
            <input type="submit" value="Login" />
        </form>
    ''')

# Simple logout route
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Unsubscribe route – only accessible if logged in
@app.route('/unsubscribe', methods=['GET', 'POST'])
@login_required
def unsubscribe():
    user_email = session['user_email']
    conn = get_db()
    if request.method == 'POST':
        reason = request.form.get('reason', None)
        unsubscribe_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Update the subscription status to "unsubscribed" (0) along with optional reason and date
        conn.execute('''
            UPDATE users
            SET subscribed = 0,
                unsubscribe_reason = ?,
                unsubscribe_date = ?
            WHERE email = ?
        ''', (reason, unsubscribe_date, user_email))
        conn.commit()
        conn.close()
        flash('You have successfully unsubscribed from the newsletter.')
        return redirect(url_for('unsubscribe'))
    
    # For GET, display the current subscription status and the unsubscription form if subscribed
    user = conn.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    conn.close()
    status_message = 'You are currently unsubscribed.' if user['subscribed'] == 0 else 'You are currently subscribed.'
    return render_template_string('''
        <h2>Newsletter Subscription</h2>
        <p>{{ status_message }}</p>
        {% if user_subscribed %}
        <form method="post">
            <label for="reason">Optional Reason for Unsubscribing:</label><br/>
            <textarea name="reason" rows="4" cols="50"></textarea><br/>
            <input type="submit" value="Unsubscribe" />
        </form>
        {% else %}
        <p>If you wish to resubscribe, please contact support.</p>
        {% endif %}
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
    ''', status_message=status_message, user_subscribed=(user['subscribed'] == 1))

if __name__ == '__main__':
    app.run(debug=True)
