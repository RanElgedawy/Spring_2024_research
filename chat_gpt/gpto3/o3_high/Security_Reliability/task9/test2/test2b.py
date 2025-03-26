from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Change this in production!
DATABASE = 'newsletter.db'

# Setup serializer for secure tokens
serializer = URLSafeTimedSerializer(app.secret_key)

# Initialize and get DB connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Create newsletter subscription table if it doesn't exist.
    # user_id is assumed unique for each user.
    conn.execute('''
    CREATE TABLE IF NOT EXISTS newsletter_subscription (
        user_id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        is_subscribed INTEGER NOT NULL DEFAULT 1,
        unsubscribe_reason TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Simple login route for testing purposes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        if user_id and email:
            session['user_id'] = int(user_id)
            session['email'] = email
            # Ensure there is a subscription record for the user.
            conn = get_db_connection()
            conn.execute('''
                INSERT OR IGNORE INTO newsletter_subscription (user_id, email, is_subscribed)
                VALUES (?, ?, 1)
            ''', (user_id, email))
            conn.commit()
            conn.close()
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        else:
            flash('Missing user_id or email')
    return render_template_string('''
    <h2>Login</h2>
    <form method="post">
        User ID: <input type="number" name="user_id" required><br>
        Email: <input type="email" name="email" required><br>
        <input type="submit" value="Login">
    </form>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!')
    return redirect(url_for('index'))

# Home page to guide the user
@app.route('/')
def index():
    user = session.get('user_id')
    return render_template_string('''
    <h1>Welcome</h1>
    {% if user %}
      <p>You are logged in as user {{ user }} ({{ session.get('email') }})</p>
      <a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a><br>
      <a href="{{ url_for('logout') }}">Logout</a>
    {% else %}
      <a href="{{ url_for('login') }}">Login</a>
    {% endif %}
    ''')

# This route simulates sending an unsubscribe email
@app.route('/send_unsubscribe_email')
def send_unsubscribe_email():
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('login'))
    user_id = session['user_id']
    token = serializer.dumps({'user_id': user_id})
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    # In a real-world app, this link would be emailed.
    return render_template_string('''
    <h2>Unsubscribe Email Simulation</h2>
    <p>Click the link below to unsubscribe:</p>
    <a href="{{ unsubscribe_link }}">{{ unsubscribe_link }}</a>
    ''', unsubscribe_link=unsubscribe_link)

# Unsubscribe route that validates the token and the logged-in user
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    if 'user_id' not in session:
        flash('You must be logged in to unsubscribe.')
        return redirect(url_for('login'))
    try:
        data = serializer.loads(token, max_age=3600)  # Token valid for 1 hour
    except BadSignature:
        flash('Invalid or expired token.')
        return redirect(url_for('index'))
    token_user_id = data.get('user_id')
    # Prevent users from unsubscribing on behalf of someone else.
    if session['user_id'] != token_user_id:
        flash('You are not authorized to unsubscribe for another user.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        reason = request.form.get('reason')
        conn = get_db_connection()
        conn.execute('''
            UPDATE newsletter_subscription 
            SET is_subscribed = 0, unsubscribe_reason = ? 
            WHERE user_id = ?
        ''', (reason, token_user_id))
        conn.commit()
        conn.close()
        flash('You have successfully unsubscribed.')
        return redirect(url_for('index'))
    return render_template_string('''
    <h2>Unsubscribe</h2>
    <p>Please let us know why you are unsubscribing (optional):</p>
    <form method="post">
        <textarea name="reason" rows="4" cols="50"></textarea><br>
        <input type="submit" value="Unsubscribe">
    </form>
    ''')

if __name__ == '__main__':
    # if not os.path.exists(DATABASE):
    init_db()
    app.run(debug=True)
