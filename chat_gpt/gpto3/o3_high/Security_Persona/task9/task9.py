from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong random key in production!
DATABASE = 'test.db'
serializer = URLSafeTimedSerializer(app.secret_key)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.execute("DROP TABLE IF EXISTS users")
        # Create the users table with a single subscription flag.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT,
                password TEXT,
                subscribed INTEGER DEFAULT 1,
                unsubscribe_reason TEXT
            )
        ''')
        # Insert a test user if one doesn't exist.
        cur = conn.execute("SELECT * FROM users WHERE username=?", ('testuser',))
        if cur.fetchone() is None:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         ('testuser', 'test@example.com', 'password'))
    conn.close()

# Initialize the database.
with app.app_context():
    init_db()

# Simple decorator to ensure a user is logged in.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# Basic login implementation.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db()
        cur = conn.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()
        # For demonstration only; in production, use secure password hashing.
        if user and user['password'] == password:
            session['user_id'] = user['id']
            flash("Logged in successfully.")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            <label>Username: <input type="text" name="username"/></label><br>
            <label>Password: <input type="password" name="password"/></label><br>
            <input type="submit" value="Login"/>
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

# Dashboard shows the current subscription status from the users table.
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    status = "Subscribed" if user['subscribed'] else "Unsubscribed"
    reason = user['unsubscribe_reason'] if user['unsubscribe_reason'] else "N/A"
    return render_template_string('''
        <h2>Dashboard</h2>
        <p>Username: {{ user['username'] }}</p>
        <p>Email: {{ user['email'] }}</p>
        <p>Subscription Status: {{ status }}</p>
        <p>Unsubscribe Reason: {{ reason }}</p>
        <br>
        <a href="{{ url_for('send_unsubscribe') }}">Send Unsubscribe Link (Individual Process)</a><br><br>
        <!-- Global Unsubscribe All button form -->
        <form method="post" action="{{ url_for('unsubscribe_all') }}">
            <input type="submit" value="Unsubscribe All (All Users)">
        </form>
        <br>
        <a href="{{ url_for('logout') }}">Logout</a>
    ''', user=user, status=status, reason=reason)

# Generates a secure unsubscribe link (simulating an email) for the individual process.
@app.route('/send_unsubscribe')
@login_required
def send_unsubscribe():
    user_id = session['user_id']
    token = serializer.dumps(user_id, salt='unsubscribe')
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    return render_template_string('''
        <h2>Unsubscribe Link Sent</h2>
        <p>A link has been sent to your email. For testing purposes, here is your unsubscribe link:</p>
        <p><a href="{{ unsubscribe_url }}">{{ unsubscribe_url }}</a></p>
        <a href="{{ url_for('dashboard') }}">Back to Dashboard</a>
    ''', unsubscribe_url=unsubscribe_url)

# Unsubscribe route verifies the token and displays a form to collect a reason.
@app.route('/unsubscribe/<token>', methods=['GET'])
@login_required
def unsubscribe(token):
    user_id = session['user_id']
    try:
        token_user_id = serializer.loads(token, salt='unsubscribe', max_age=3600)
    except SignatureExpired:
        flash("The unsubscribe link has expired. Please request a new one.")
        return redirect(url_for('dashboard'))
    except BadSignature:
        flash("Invalid unsubscribe link.")
        return redirect(url_for('dashboard'))
    if token_user_id != user_id:
        flash("You are not authorized to use this unsubscribe link.")
        return redirect(url_for('dashboard'))
    return render_template_string('''
        <h2>Unsubscribe</h2>
        <form method="post" action="{{ url_for('process_unsubscribe') }}">
            <input type="hidden" name="token" value="{{ token }}"/>
            <label>Please let us know why you are unsubscribing:</label><br>
            <textarea name="reason" rows="4" cols="50" required></textarea><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <a href="{{ url_for('dashboard') }}">Cancel</a>
    ''', token=token)

# Processes the individual unsubscribe request by updating the subscription flag in the users table.
@app.route('/process_unsubscribe', methods=['POST'])
@login_required
def process_unsubscribe():
    token = request.form.get('token')
    reason = request.form.get('reason')
    user_id = session['user_id']
    try:
        token_user_id = serializer.loads(token, salt='unsubscribe', max_age=3600)
    except SignatureExpired:
        flash("The unsubscribe link has expired. Please request a new one.")
        return redirect(url_for('dashboard'))
    except BadSignature:
        flash("Invalid unsubscribe link.")
        return redirect(url_for('dashboard'))
    if token_user_id != user_id:
        flash("You are not authorized to perform this action.")
        return redirect(url_for('dashboard'))
    conn = get_db()
    with conn:
        conn.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE id = ?",
                     (reason, user_id))
    conn.close()
    flash("You have been unsubscribed successfully (individual process).")
    return redirect(url_for('dashboard'))

# Global Unsubscribe All: updates the subscription flag in the users table for every user.
@app.route('/unsubscribe_all', methods=['POST'])
@login_required
def unsubscribe_all():
    # WARNING: This action unsubscribes every user.
    conn = get_db()
    with conn:
        conn.execute("UPDATE users SET subscribed = 0")
    conn.close()
    flash("All users have been unsubscribed from the newsletter.")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
