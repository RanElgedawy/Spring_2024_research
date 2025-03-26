from flask import Flask, request, session, redirect, url_for, render_template_string, g
import sqlite3

DATABASE = 'newsletter.db'
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session encryption

# ---------------- Database Functions ----------------

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Enable name-based access to columns
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database with necessary tables and a test user/subscriber."""
    with app.app_context():
        db = get_db()
        # Create newsletter subscription table
        db.execute("DROP TABLE IF EXISTS newsletter_subscribers")
        db.execute("DROP TABLE IF EXISTS users")
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                is_subscribed INTEGER NOT NULL DEFAULT 1,
                unsubscribe_reason TEXT
            );
        ''')
        # Create users table (for identity verification)
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        # Insert a test user and corresponding newsletter subscriber record if they don't already exist.
        try:
            db.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@example.com", "password"))
            db.execute("INSERT INTO newsletter_subscribers (email) VALUES (?)", ("test@example.com",))
            db.commit()
        except sqlite3.IntegrityError:
            # Test user already exists
            pass

# ---------------- HTML Templates ----------------

LOGIN_TEMPLATE = """
<!doctype html>
<title>Login</title>
<h1>Login</h1>
{% if error %}
<p style="color: red;">{{ error }}</p>
{% endif %}
<form method="post">
  <label>Email:</label>
  <input type="email" name="email" required><br><br>
  <label>Password:</label>
  <input type="password" name="password" required><br><br>
  <input type="submit" value="Login">
</form>
"""

UNSUBSCRIBE_TEMPLATE = """
<!doctype html>
<title>Unsubscribe</title>
<h1>Unsubscribe from Newsletter</h1>
<form method="post">
  <label for="reason">Optional: Reason for unsubscribing:</label><br>
  <textarea name="reason" id="reason" rows="4" cols="50"></textarea><br><br>
  <input type="submit" value="Unsubscribe">
</form>
"""

# ---------------- Routes ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Allows a user to log in using email and password."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        if user:
            session['email'] = user['email']
            return redirect(url_for('profile'))
        else:
            error = "Invalid credentials"
            return render_template_string(LOGIN_TEMPLATE, error=error)
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    """Displays the logged-in user's current newsletter subscription status."""
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    db = get_db()
    subscriber = db.execute("SELECT * FROM newsletter_subscribers WHERE email = ?", (email,)).fetchone()
    status = "Subscribed" if subscriber and subscriber['is_subscribed'] == 1 else "Unsubscribed"
    return f"<h1>Profile</h1><p>Hello, {email}.</p><p>Newsletter status: <strong>{status}</strong></p><p><a href='{url_for('unsubscribe')}'>Unsubscribe from Newsletter</a></p><p><a href='{url_for('logout')}'>Logout</a></p>"

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """
    Provides a form for a logged-in user to unsubscribe from the newsletter.
    Optionally, the user can provide a reason for unsubscribing.
    The user's identity is verified using the session, and the subscription record is updated.
    """
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    db = get_db()
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        # Update the subscription status and record the optional reason
        db.execute(
            "UPDATE newsletter_subscribers SET is_subscribed = 0, unsubscribe_reason = ? WHERE email = ?",
            (reason, email)
        )
        db.commit()
        return f"<h1>Unsubscribed</h1><p>{email} has been unsubscribed from the newsletter.</p><p><a href='{url_for('profile')}'>Back to Profile</a></p>"
    return render_template_string(UNSUBSCRIBE_TEMPLATE)

# ---------------- Main Entry Point ----------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
