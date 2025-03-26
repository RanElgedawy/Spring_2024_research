from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from functools import wraps

app = Flask(__name__)
app.secret_key = 'replace_with_a_secure_random_secret_key'  # Change this to a secure random key
DATABASE = 'app.db'

# Setup the serializer for secure token generation (expires in 1 hour)
serializer = URLSafeTimedSerializer(app.secret_key)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create a users table if it doesn't exist. In a real app, this table might already exist.
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
    # Insert a test user if not already present
    c.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
    if c.fetchone() is None:
        c.execute("INSERT INTO users (email, password, subscribed) VALUES (?, ?, ?)", 
                  ("test@example.com", "password", 1))
    conn.commit()
    conn.close()

init_db()

# --- Helper: login_required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template_string('''
            <h1>Welcome, {{ email }}</h1>
            <p>Your subscription status: {% if subscribed %}Subscribed{% else %}Unsubscribed{% endif %}</p>
            <p><a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a></p>
            <p><a href="{{ url_for('logout') }}">Logout</a></p>
        ''', email=session.get('email'), subscribed=session.get('subscribed', True))
    return render_template_string('''
        <h1>Welcome</h1>
        <p><a href="{{ url_for('login') }}">Login</a></p>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id, email, password, subscribed FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['email'] = user[1]
            session['subscribed'] = bool(user[3])
            flash("Logged in successfully.")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.")
    return render_template_string('''
        <h1>Login</h1>
        <form method="POST">
            Email: <input type="email" name="email" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
        <p><a href="{{ url_for('index') }}">Home</a></p>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('index'))

@app.route('/send_unsubscribe_email')
@login_required
def send_unsubscribe_email():
    # Generate a secure token that includes the user's ID
    token = serializer.dumps({'user_id': session['user_id']})
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    # In a real application, you would send this link via email.
    return render_template_string('''
        <h1>Unsubscribe Email Sent</h1>
        <p>In a real application, an email would be sent to you with the unsubscribe link.</p>
        <p>For testing purposes, use the link below:</p>
        <p><a href="{{ unsubscribe_link }}">{{ unsubscribe_link }}</a></p>
        <p><a href="{{ url_for('index') }}">Home</a></p>
    ''', unsubscribe_link=unsubscribe_link)

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
@login_required
def unsubscribe(token):
    try:
        # Validate and decode the token (expires after 1 hour)
        data = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        flash("The unsubscribe link has expired.")
        return redirect(url_for('index'))
    except BadSignature:
        flash("Invalid unsubscribe link.")
        return redirect(url_for('index'))
    
    # Verify that the token belongs to the logged in user
    if data.get('user_id') != session['user_id']:
        flash("Unauthorized unsubscribe attempt.")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        # Update the user's subscription status and store the reason for unsubscribing
        c.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE id = ?", (reason, session['user_id']))
        conn.commit()
        conn.close()
        session['subscribed'] = False
        flash("You have successfully unsubscribed.")
        return redirect(url_for('index'))
    
    return render_template_string('''
        <h1>Unsubscribe</h1>
        <p>Please let us know why you are unsubscribing (optional):</p>
        <form method="POST">
            <textarea name="reason" rows="4" cols="50"></textarea><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <p><a href="{{ url_for('index') }}">Home</a></p>
    ''')

if __name__ == "__main__":
    app.run(debug=True)
