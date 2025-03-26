from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions and token signing
serializer = URLSafeTimedSerializer(app.secret_key)

DATABASE = 'subscriptions.db'

# HTML templates
login_template = """
<h2>Login Simulation</h2>
<p>You are logged in as: {{ email }}</p>
<p><a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a></p>
<p><a href="{{ url_for('logout') }}">Logout</a></p>
"""

unsubscribe_form_template = """
<h2>Unsubscribe</h2>
<p>User: {{ email }}</p>
<form method="post">
  <label for="reason">Please tell us why you are unsubscribing:</label><br>
  <textarea name="reason" id="reason" rows="4" cols="50" required></textarea><br>
  <button type="submit">Unsubscribe</button>
</form>
"""

message_template = """
<h2>{{ title }}</h2>
<p>{{ message }}</p>
<p><a href="{{ url_for('index') }}">Return Home</a></p>
"""

index_template = """
<h2>Home</h2>
{% if email %}
  <p>Logged in as: {{ email }}</p>
  <p><a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a></p>
  <p><a href="{{ url_for('logout') }}">Logout</a></p>
{% else %}
  <p>You are not logged in.</p>
  <p>To login, visit: /login?user_id=YOUR_ID&email=YOUR_EMAIL</p>
{% endif %}
"""

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS subscriptions")
    
    # Create subscriptions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            subscribed INTEGER NOT NULL DEFAULT 1,
            unsubscribe_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    email = session.get('email')
    return render_template_string(index_template, email=email)

# Simple login simulation route (for testing only)
@app.route('/login')
def login():
    user_id = request.args.get('user_id')
    email = request.args.get('email')
    if not user_id or not email:
        return "Please provide user_id and email as query parameters.", 400

    # Set session info
    session['user_id'] = user_id
    session['email'] = email

    # Ensure the user exists in the subscriptions table
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO subscriptions (user_id, email, subscribed) VALUES (?, ?, ?)",
                   (user_id, email, 1))
    conn.commit()
    conn.close()

    return render_template_string(login_template, email=email)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

# Route to simulate sending the unsubscribe email
@app.route('/send_unsubscribe_email')
def send_unsubscribe_email():
    if 'user_id' not in session:
        return "Access denied. Please log in.", 401

    user_id = session['user_id']
    email = session['email']
    # Create a token that includes the user_id and email
    token = serializer.dumps({'user_id': user_id, 'email': email})
    # Generate an unsubscribe URL with the token
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    # In a real application, you would send this URL via email.
    # Here, we simply display it.
    return f"Simulated unsubscribe email sent to {email}. Click <a href='{unsubscribe_url}'>here</a> to unsubscribe."

# Unsubscribe route that handles both GET (form display) and POST (process form submission)
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    if 'user_id' not in session:
        return "Access denied. Please log in.", 401

    try:
        # Validate token; expires in 3600 seconds (1 hour)
        data = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        return "The unsubscribe link has expired.", 400
    except BadSignature:
        return "Invalid unsubscribe link.", 400

    # Ensure the token user matches the logged-in user
    if data.get('user_id') != session.get('user_id'):
        return "You are not authorized to unsubscribe using this link.", 403

    email = session.get('email')
    if request.method == 'POST':
        reason = request.form.get('reason')
        if not reason:
            flash("Please provide a reason.")
            return render_template_string(unsubscribe_form_template, email=email)
        # Update subscription preferences in the database securely using parameterized query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE subscriptions
            SET subscribed = 0,
                unsubscribe_reason = ?
            WHERE user_id = ? AND email = ?
        """, (reason, session['user_id'], email))
        conn.commit()
        conn.close()
        return render_template_string(message_template, title="Unsubscribed", message="You have successfully unsubscribed from our newsletter.")
    else:
        # Display the unsubscribe form
        return render_template_string(unsubscribe_form_template, email=email)

if __name__ == '__main__':
    app.run(debug=True)
