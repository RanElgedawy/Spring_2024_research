import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string, flash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-secret-key'
serializer = URLSafeTimedSerializer(app.secret_key)

# Database initialization: creates tables for users and subscriptions.
def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS subscriptions")
    # Users table (assume this exists in production)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    email TEXT UNIQUE
                )''')
    # Subscriptions table holds the subscription status and an optional unsubscribe reason.
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    is_subscribed INTEGER DEFAULT 1,
                    unsubscribe_reason TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    # Insert a test user if not exists.
    c.execute("SELECT id FROM users WHERE username = ?", ("testuser",))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  ("testuser", "password", "testuser@example.com"))
        user_id = c.lastrowid
        c.execute("INSERT INTO subscriptions (user_id, is_subscribed) VALUES (?, ?)", (user_id, 1))
    else:
        user_id = user[0]
        # Ensure a subscription record exists.
        c.execute("SELECT user_id FROM subscriptions WHERE user_id = ?", (user_id,))
        if not c.fetchone():
            c.execute("INSERT INTO subscriptions (user_id, is_subscribed) VALUES (?, ?)", (user_id, 1))
    conn.commit()
    conn.close()

init_db()

# Helper to get a database connection.
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Simple login_required decorator.
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Login route: for testing, use username: testuser, password: password.
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = '''
    <h2>Login</h2>
    <form method="post">
      Username: <input type="text" name="username"><br>
      Password: <input type="password" name="password"><br>
      <input type="submit" value="Log In">
    </form>
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Logged in successfully.")
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            flash("Invalid credentials.")
    return render_template_string(login_form)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('index'))

@app.route('/')
def index():
    user = session.get('username')
    return render_template_string('''
        <h1>Welcome {{ user or "Guest" }}</h1>
        {% if user %}
            <p><a href="{{ url_for('request_unsubscribe') }}">Request Unsubscribe Email</a></p>
            <p><a href="{{ url_for('unsubscribe_all') }}">Unsubscribe All Users</a></p>
            <p><a href="{{ url_for('logout') }}">Logout</a></p>
        {% else %}
            <p><a href="{{ url_for('login') }}">Login</a></p>
        {% endif %}
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul>
          {% endif %}
        {% endwith %}
    ''', user=user)

# Route where logged-in user can request an unsubscribe email.
@app.route('/request_unsubscribe')
@login_required
def request_unsubscribe():
    user_id = session['user_id']
    # Generate a token that encodes the user_id.
    token = serializer.dumps({'user_id': user_id})
    # In production, you would email this link. For testing, we display it.
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    flash("Unsubscribe email sent! (For testing, please click the link below.)")
    return render_template_string('''
        <h2>Unsubscribe Email</h2>
        <p>Click the following link to unsubscribe:</p>
        <p><a href="{{ unsubscribe_link }}">{{ unsubscribe_link }}</a></p>
        <p><a href="{{ url_for('index') }}">Back to Home</a></p>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul>
          {% endif %}
        {% endwith %}
    ''', unsubscribe_link=unsubscribe_link)

# Route that handles the unsubscribe link with a token.
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
@login_required
def unsubscribe(token):
    try:
        # Token expires in 1 hour.
        data = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        flash("The unsubscribe link has expired. Please request a new one.")
        return redirect(url_for('request_unsubscribe'))
    except BadSignature:
        flash("Invalid unsubscribe link.")
        return redirect(url_for('index'))
    
    # Ensure the token corresponds to the logged in user.
    if data.get('user_id') != session['user_id']:
        flash("Unauthorized unsubscribe attempt.")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        conn = get_db_connection()
        conn.execute("UPDATE subscriptions SET is_subscribed = 0, unsubscribe_reason = ? WHERE user_id = ?",
                     (reason, session['user_id']))
        conn.commit()
        conn.close()
        flash("You have been unsubscribed. Thank you for your feedback!")
        return redirect(url_for('index'))
    
    unsubscribe_form = '''
    <h2>Unsubscribe</h2>
    <p>Please tell us why you are unsubscribing (optional):</p>
    <form method="post">
      <textarea name="reason" rows="4" cols="50"></textarea><br>
      <input type="submit" value="Unsubscribe">
    </form>
    <p><a href="{{ url_for('index') }}">Cancel</a></p>
    '''
    return render_template_string(unsubscribe_form)

# Updated route to handle "Unsubscribe All" that unsubscribes every user
# by updating the same boolean value in the subscriptions table.
@app.route('/unsubscribe_all', methods=['GET', 'POST'])
@login_required
def unsubscribe_all():
    if request.method == 'POST':
        conn = get_db_connection()
        # Update all users so that is_subscribed is set to 0.
        conn.execute("UPDATE subscriptions SET is_subscribed = 0")
        conn.commit()
        conn.close()
        flash("All users have been unsubscribed.")
        return redirect(url_for('index'))
    # Render a confirmation page before unsubscribing all users.
    return render_template_string('''
        <h2>Unsubscribe All Users</h2>
        <p>Are you sure you want to unsubscribe ALL users from the service?</p>
        <form method="post">
          <input type="submit" value="Yes, Unsubscribe All">
        </form>
        <p><a href="{{ url_for('index') }}">Cancel</a></p>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
