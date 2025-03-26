from flask import Flask, request, redirect, url_for, render_template_string, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'replace_with_a_secret_key'  # Replace with a proper secret key in production

DATABASE = 'newsletter.db'

# HTML Templates (using simple strings for self-contained example)
login_template = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="get" action="{{ url_for('set_login') }}">
    <label>Email: <input type="email" name="email" required></label>
    <button type="submit">Login</button>
</form>
"""

unsubscribe_template = """
<!doctype html>
<title>Unsubscribe</title>
<h2>Unsubscribe from Newsletter</h2>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color: red;">
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<p>Logged in as: <strong>{{ email }}</strong></p>
{% if not subscribed %}
<p>You have already unsubscribed.</p>
{% else %}
<form method="post" action="{{ url_for('unsubscribe') }}">
    <label>Reason for unsubscription (optional):</label><br>
    <textarea name="reason" rows="4" cols="50" placeholder="Optional"></textarea><br><br>
    <button type="submit">Unsubscribe</button>
</form>
{% endif %}
"""

result_template = """
<!doctype html>
<title>Unsubscribe Confirmation</title>
<h2>Unsubscribe Confirmation</h2>
<p>{{ message }}</p>
<a href="{{ url_for('unsubscribe') }}">Back</a>
"""

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with the newsletter_subscriptions table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_subscribed INTEGER NOT NULL DEFAULT 1,
            unsubscribe_reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_test_user(email):
    """Adds a test user to the database if not already present."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO newsletter_subscriptions (email) VALUES (?)", (email,))
        conn.commit()
    except sqlite3.IntegrityError:
        # User already exists
        pass
    finally:
        conn.close()

@app.before_first_request
def setup():
    """Initialize database and add a test user before the first request."""
    init_db()
    # For testing purposes, create a test user
    test_email = "test@example.com"
    add_test_user(test_email)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
    """Simple login page where the user enters their email."""
    return render_template_string(login_template)

@app.route('/set_login', methods=['GET'])
def set_login():
    """Sets the user's email in session and redirects to unsubscribe."""
    email = request.args.get('email')
    if email:
        session['email'] = email
        # For testing, ensure the user exists in the DB
        add_test_user(email)
        return redirect(url_for('unsubscribe'))
    flash("Email is required to login.")
    return redirect(url_for('login'))

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    email = session.get('email')
    if not email:
        flash("Please log in first.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM newsletter_subscriptions WHERE email = ?", (email,))
    user = cur.fetchone()

    if request.method == 'POST':
        if not user:
            flash("User not found.")
            return redirect(url_for('unsubscribe'))
        if user['is_subscribed'] == 0:
            flash("You have already unsubscribed.")
            return redirect(url_for('unsubscribe'))

        reason = request.form.get('reason', '').strip()
        cur.execute("""
            UPDATE newsletter_subscriptions 
            SET is_subscribed = 0, unsubscribe_reason = ?
            WHERE email = ?
        """, (reason if reason else None, email))
        conn.commit()
        conn.close()
        message = "You have successfully unsubscribed from the newsletter."
        if reason:
            message += " Your reason: " + reason
        return render_template_string(result_template, message=message)

    conn.close()
    # Show unsubscribe page with current subscription status.
    subscribed = user['is_subscribed'] == 1 if user else False
    return render_template_string(unsubscribe_template, email=email, subscribed=subscribed)

if __name__ == '__main__':
    # Run the Flask app. For testing, access /login to log in with your email.
    app.run(debug=True)
