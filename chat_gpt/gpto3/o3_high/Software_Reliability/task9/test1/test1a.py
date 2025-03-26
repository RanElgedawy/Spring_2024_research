from flask import Flask, request, render_template_string, session, redirect, url_for, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key in production

DATABASE = 'newsletter.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS subscriptions")
        db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                email TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                reason TEXT,
                unsubscribed_at TIMESTAMP
            )
        ''')
        db.commit()

init_db()

# --- Dummy Login for Testing ---
# This login endpoint allows you to “log in” by entering your email.
# It also ensures that a record for the email exists in the subscriptions table.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            return "Email required", 400
        session['user_email'] = email
        db = get_db()
        cursor = db.execute('SELECT * FROM subscriptions WHERE email = ?', (email,))
        if cursor.fetchone() is None:
            # If user not already in DB, add with default "subscribed" status.
            db.execute('INSERT INTO subscriptions (email, status) VALUES (?, ?)', (email, 'subscribed'))
            db.commit()
        return redirect(url_for('status'))
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            <label>Email: <input type="email" name="email" required></label>
            <button type="submit">Login</button>
        </form>
    ''')

# --- View Subscription Status ---
@app.route('/status')
def status():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    email = session['user_email']
    db = get_db()
    cursor = db.execute('SELECT * FROM subscriptions WHERE email = ?', (email,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    return render_template_string('''
        <h2>Subscription Status</h2>
        <p><strong>Email:</strong> {{ user['email'] }}</p>
        <p><strong>Status:</strong> {{ user['status'] }}</p>
        {% if user['reason'] %}
        <p><strong>Reason for Unsubscription:</strong> {{ user['reason'] }}</p>
        {% endif %}
        {% if user['unsubscribed_at'] %}
        <p><strong>Unsubscribed At:</strong> {{ user['unsubscribed_at'] }}</p>
        {% endif %}
        <a href="{{ url_for('unsubscribe') }}">Unsubscribe from Newsletter</a>
    ''', user=user)

# --- Unsubscribe Endpoint ---
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    email = session['user_email']
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        db = get_db()
        # Verify user identity by checking that the email exists in the DB.
        cursor = db.execute('SELECT * FROM subscriptions WHERE email = ?', (email,))
        if cursor.fetchone() is None:
            return "User not found", 404
        # Update subscription status, record the optional reason, and log the time.
        db.execute('''
            UPDATE subscriptions
            SET status = ?, reason = ?, unsubscribed_at = ?
            WHERE email = ?
        ''', ('unsubscribed', reason, datetime.now(), email))
        db.commit()
        return redirect(url_for('status'))
    return render_template_string('''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="POST">
            <label>Reason for unsubscription (optional):</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br>
            <button type="submit">Unsubscribe</button>
        </form>
        <a href="{{ url_for('status') }}">Back to Status</a>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
