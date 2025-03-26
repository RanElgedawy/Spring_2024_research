import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string, flash
from itsdangerous import URLSafeSerializer, BadSignature
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this in production
DATABASE = 'newsletter.db'
serializer = URLSafeSerializer(app.secret_key, salt='unsubscribe-salt')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS subscriptions")
    
    # Create a users table if it doesn't exist.
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    # Create a subscriptions table if it doesn't exist.
    cur.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        is_subscribed INTEGER NOT NULL DEFAULT 1,
        unsubscribe_reason TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    # Insert a test user if it doesn't exist.
    cur.execute("SELECT * FROM users WHERE email = ?", ('test@example.com',))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", ('test@example.com', 'password'))
        user_id = cur.lastrowid
        cur.execute("INSERT INTO subscriptions (user_id, is_subscribed) VALUES (?, ?)", (user_id, 1))
        conn.commit()
    conn.close()

init_db()

# A simple decorator to require login.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access that page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login route for testing purposes.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            flash('Logged in successfully.')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
          Email: <input type="text" name="email"><br>
          Password: <input type="password" name="password"><br>
          <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Dashboard to display current subscription status.
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
    sub = cur.fetchone()
    conn.close()
    status = "Subscribed" if sub and sub['is_subscribed'] else "Unsubscribed"
    return render_template_string('''
        <h2>Dashboard</h2>
        <p>Your subscription status: {{ status }}</p>
        <p><a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a></p>
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
    ''', status=status)

# Route to simulate sending an unsubscribe email with a secure link.
@app.route('/send_unsubscribe_email')
@login_required
def send_unsubscribe_email():
    user_id = session['user_id']
    # Generate a secure token containing the user's id.
    token = serializer.dumps({'user_id': user_id})
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    # In a real application, you would send this link via email.
    return render_template_string('''
        <h2>Unsubscribe Email Simulation</h2>
        <p>An unsubscribe link has been sent to your email (simulated below):</p>
        <p><a href="{{ unsubscribe_link }}">{{ unsubscribe_link }}</a></p>
        <p><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></p>
    ''', unsubscribe_link=unsubscribe_link)

# Unsubscribe route: GET shows a form; POST processes the unsubscribe request.
@app.route('/unsubscribe', methods=['GET', 'POST'])
@login_required
def unsubscribe():
    # Retrieve token from URL (GET) or from form (POST).
    token = request.args.get('token') if request.method == 'GET' else request.form.get('token')
    if not token:
        flash('Missing token.')
        return redirect(url_for('dashboard'))
    try:
        data = serializer.loads(token)
    except BadSignature:
        flash('Invalid or expired token.')
        return redirect(url_for('dashboard'))
    
    # Ensure the token's user_id matches the logged in user.
    if data.get('user_id') != session.get('user_id'):
        flash('Unauthorized access.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        user_id = session['user_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE subscriptions SET is_subscribed = 0, unsubscribe_reason = ? WHERE user_id = ?", (reason, user_id))
        conn.commit()
        conn.close()
        flash('You have been unsubscribed.')
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
        <h2>Unsubscribe</h2>
        <form method="post">
            <input type="hidden" name="token" value="{{ token }}">
            <p>Please let us know why you are unsubscribing (optional):</p>
            <textarea name="reason" rows="4" cols="50"></textarea><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <p><a href="{{ url_for('dashboard') }}">Cancel</a></p>
    ''', token=token)

if __name__ == '__main__':
    app.run(debug=True)
