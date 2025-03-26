import sqlite3
import os
from datetime import datetime, timedelta
import secrets
from flask import Flask, request, render_template, redirect, url_for, session, g

DATABASE = 'newsletter.db'
SECRET_KEY = 'your_secret_key'  # Replace with a strong, random key

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

database_initialized = False

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

def initialize_database():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.executescript("""
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS newsletter_subscriptions;
            DROP TABLE IF EXISTS unsubscribe_tokens;
                
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL -- In a real app, use proper hashing
            );

            CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
                user_id INTEGER PRIMARY KEY,
                is_subscribed INTEGER NOT NULL DEFAULT 1, -- 1 for subscribed, 0 for unsubscribed
                unsubscribe_reason TEXT,
                unsubscribe_timestamp DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS unsubscribe_tokens (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expiry_timestamp DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        con.commit()

# --- Helper Functions ---

def generate_unsubscribe_token(user_id):
    token = secrets.token_urlsafe(32)
    expiry_timestamp = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    execute_db("INSERT INTO unsubscribe_tokens (token, user_id, expiry_timestamp) VALUES (?, ?, ?)",
               (token, user_id, expiry_timestamp))
    return token

def get_user_by_id(user_id):
    return query_db("SELECT id, email FROM users WHERE id = ?", (user_id,), one=True)

def get_user_by_email(email):
    return query_db("SELECT id, email, password FROM users WHERE email = ?", (email,), one=True)

def is_user_subscribed(user_id):
    subscription = query_db("SELECT is_subscribed FROM newsletter_subscriptions WHERE user_id = ?", (user_id,), one=True)
    return subscription['is_subscribed'] if subscription else None

def unsubscribe_user(user_id, reason):
    execute_db("""
        INSERT OR REPLACE INTO newsletter_subscriptions (user_id, is_subscribed, unsubscribe_reason, unsubscribe_timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, 0, reason, datetime.utcnow()))

def get_user_from_token(token):
    token_data = query_db("SELECT user_id, expiry_timestamp FROM unsubscribe_tokens WHERE token = ?", (token,), one=True)
    if token_data and datetime.utcnow() < datetime.fromisoformat(token_data['expiry_timestamp']):
        return get_user_by_id(token_data['user_id'])
    return None

def invalidate_token(token):
    execute_db("DELETE FROM unsubscribe_tokens WHERE token = ?", (token,))

# --- Authentication (Simplified for demonstration) ---

def login_user(user):
    session['user_id'] = user['id']

def logout_user():
    session.pop('user_id', None)

def get_logged_in_user_id():
    return session.get('user_id')

def require_login():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if get_logged_in_user_id() is None:
                return "You need to be logged in to access this.", 401
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_same_user(user_id_param):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logged_in_user_id = get_logged_in_user_id()
            requested_user_id = kwargs.get(user_id_param)
            if logged_in_user_id is None or int(logged_in_user_id) != int(requested_user_id):
                return "You are not authorized to access this user's information.", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    global database_initialized
    if not database_initialized:
        if not os.path.exists(DATABASE):
            initialize_database()
        database_initialized = True
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'] # In a real app, hash this!
        error = None
        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif get_user_by_email(email) is not None:
            error = 'User with this email already exists.'

        if error is None:
            execute_db("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            user = get_user_by_email(email)
            login_user(user)

            # Subscribe the new user to the newsletter by default
            execute_db("INSERT INTO newsletter_subscriptions (user_id, is_subscribed) VALUES (?, ?)", (user['id'], 1))

            return redirect(url_for('profile'))
        flash(error)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global database_initialized
    if not database_initialized:
        if not os.path.exists(DATABASE):
            initialize_database()
        database_initialized = True
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'] # In a real app, compare with hashed password
        error = None
        user = get_user_by_email(email)

        if user is None:
            error = 'Incorrect username.'
        elif user is not None and user['password'] != password: # Ensure user is not None before accessing 'password'
            error = 'Incorrect password.'

        if error is None and user is not None: # Ensure user is not None before logging in
            login_user(user)
            return redirect(url_for('profile'))
        flash(error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    # (Your logout route logic remains the same)
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@require_login()
def profile():
    global database_initialized
    if not database_initialized:
        if not os.path.exists(DATABASE):
            initialize_database()
        database_initialized = True
    # (Rest of your profile route logic remains the same)
    user_id = get_logged_in_user_id()
    user = get_user_by_id(user_id)
    is_subscribed_val = is_user_subscribed(user_id)
    subscribed_status = "Subscribed" if is_subscribed_val == 1 else "Not Subscribed"
    return render_template('profile.html', user=user, subscribed_status=subscribed_status)

@app.route('/')
def index():
    global database_initialized
    if not database_initialized:
        if not os.path.exists(DATABASE):
            initialize_database()
        database_initialized = True
    return render_template('index.html')

@app.route('/unsubscribe/request')
@require_login()
def request_unsubscribe():
    global database_initialized
    if not database_initialized:
        if not os.path.exists(DATABASE):
            initialize_database()
        database_initialized = True
    # (Rest of your request_unsubscribe route logic remains the same)
    user_id = get_logged_in_user_id()
    user = get_user_by_id(user_id)
    if user:
        unsubscribe_token = generate_unsubscribe_token(user_id)
        unsubscribe_link = url_for('unsubscribe', token=unsubscribe_token, _external=True)
        # In a real application, you would send this link to the user's email
        print(f"Unsubscribe Link for {user['email']}: {unsubscribe_link}")
        return render_template('unsubscribe_request_sent.html', email=user['email'])
    return "Error: Could not find user.", 404

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    global database_initialized
    if not database_initialized:
        if not os.path.exists(DATABASE):
            initialize_database()
        database_initialized = True
    # (Rest of your unsubscribe route logic remains the same)
    user = get_user_from_token(token)
    if not user:
        return render_template('unsubscribe_invalid_token.html')

    if request.method == 'POST':
        reason = request.form.get('reason')
        unsubscribe_user(user['id'], reason)
        invalidate_token(token)
        return render_template('unsubscribe_success.html')

    return render_template('unsubscribe_form.html', token=token)

@app.route('/unsubscribe/all', methods=['POST'])
@require_login()
def unsubscribe_all():
    if get_logged_in_user_id() == 1:  # Replace 1 with the actual admin user ID check
        execute_db("UPDATE newsletter_subscriptions SET is_subscribed = 0")
        flash("Successfully unsubscribed all users from the newsletter.")
        return redirect(url_for('profile'))
    else:
        return "You are not authorized to perform this action.", 403
    
# --- Basic HTML Templates ---
# (Your HTML templates remain the same)

if __name__ == '__main__':
    from flask import flash
    app.run(debug=True)