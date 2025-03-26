from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key in production
DATABASE = 'app.db'
serializer = URLSafeTimedSerializer(app.secret_key)

def get_db():
    """Establishes a connection to the SQLite database."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Creates necessary tables and inserts dummy users if the users table is empty."""
    with get_db() as db:
        db.execute("DROP TABLE IF EXISTS users")
        db.execute("DROP TABLE IF EXISTS unsubscribe_reasons")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                is_subscribed BOOLEAN NOT NULL DEFAULT 1
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS unsubscribe_reasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Insert dummy users for testing if no users exist
        cur = db.execute('SELECT COUNT(*) as count FROM users')
        count = cur.fetchone()['count']
        if count == 0:
            db.execute("INSERT INTO users (username, email) VALUES (?, ?)", ('alice', 'alice@example.com'))
            db.execute("INSERT INTO users (username, email) VALUES (?, ?)", ('bob', 'bob@example.com'))
        db.commit()

@app.before_first_request
def initialize():
    """Initializes the database before the first request."""
    init_db()

# Simple authentication decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home page with basic instructions
@app.route('/')
def index():
    return render_template_string('''
    <h1>Welcome to the Newsletter Unsubscribe Demo</h1>
    {% if 'user_id' in session %}
      <p>Logged in as {{ session['username'] }} (<a href="{{ url_for('logout') }}">Logout</a>)</p>
      <p><a href="{{ url_for('dashboard') }}">Go to Dashboard</a></p>
    {% else %}
      <p><a href="{{ url_for('login') }}">Login</a></p>
    {% endif %}
    ''')

# Login route for testing
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # For testing, the user selects a user by id
        user_id = request.form.get('user_id')
        if user_id:
            db = get_db()
            cur = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash("Logged in successfully.")
                return redirect(url_for('dashboard'))
            else:
                flash("User not found.")
    db = get_db()
    cur = db.execute('SELECT * FROM users')
    users = cur.fetchall()
    return render_template_string('''
    <h1>Login</h1>
    <form method="post">
        <label for="user_id">Select User:</label>
        <select name="user_id">
        {% for user in users %}
            <option value="{{ user['id'] }}">{{ user['username'] }} ({{ user['email'] }})</option>
        {% endfor %}
        </select>
        <input type="submit" value="Login">
    </form>
    <p><a href="{{ url_for('index') }}">Home</a></p>
    ''', users=users)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('index'))

# User dashboard shows current subscription status and option to send an unsubscribe email
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cur.fetchone()
    subscription_status = "Subscribed" if user['is_subscribed'] else "Unsubscribed"
    return render_template_string('''
    <h1>Dashboard</h1>
    <p>Hello, {{ session['username'] }}!</p>
    <p>Your subscription status: {{ subscription_status }}</p>
    {% if user['is_subscribed'] %}
      <form action="{{ url_for('send_unsubscribe_email') }}" method="post">
        <input type="submit" value="Send Unsubscribe Email">
      </form>
    {% else %}
      <p>You are already unsubscribed.</p>
    {% endif %}
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
    ''', session=session, subscription_status=subscription_status, user=user)

# Route to simulate sending an unsubscribe email
@app.route('/send_unsubscribe_email', methods=['POST'])
@login_required
def send_unsubscribe_email():
    user_id = session['user_id']
    token = serializer.dumps({'user_id': user_id})
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    # Simulate sending email by printing the link to the console
    print(f"Simulated email to user: Click this link to unsubscribe: {unsubscribe_link}")
    flash("Unsubscribe email sent! (Check your console output for the link in this demo.)")
    return redirect(url_for('dashboard'))

# Unsubscribe route that validates the token, asks for a reason, and updates the subscription status
@app.route('/unsubscribe', methods=['GET', 'POST'])
@login_required
def unsubscribe():
    token = request.args.get('token')
    if not token:
        flash("Invalid unsubscribe link.")
        return redirect(url_for('dashboard'))
    try:
        data = serializer.loads(token, max_age=3600)  # Token valid for 1 hour
    except SignatureExpired:
        flash("The unsubscribe link has expired.")
        return redirect(url_for('dashboard'))
    except BadSignature:
        flash("Invalid unsubscribe token.")
        return redirect(url_for('dashboard'))
    
    # Ensure the token belongs to the logged-in user
    if data.get('user_id') != session.get('user_id'):
        flash("You are not authorized to perform this action.")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        db = get_db()
        # Update the user's subscription status to unsubscribed
        db.execute('UPDATE users SET is_subscribed = 0 WHERE id = ?', (session['user_id'],))
        # Record the unsubscribe reason
        db.execute('INSERT INTO unsubscribe_reasons (user_id, reason) VALUES (?, ?)', (session['user_id'], reason))
        db.commit()
        flash("You have been unsubscribed. Thank you for your feedback.")
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <h1>Unsubscribe</h1>
    <p>Please let us know why you're unsubscribing:</p>
    <form method="post">
        <textarea name="reason" rows="4" cols="50" placeholder="Your reason..."></textarea><br>
        <input type="submit" value="Unsubscribe">
    </form>
    <p><a href="{{ url_for('dashboard') }}">Cancel</a></p>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
