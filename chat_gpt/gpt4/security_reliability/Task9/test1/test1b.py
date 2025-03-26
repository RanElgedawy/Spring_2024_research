from flask import Flask, request, redirect, render_template_string, url_for
from itsdangerous import URLSafeTimedSerializer
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change to a strong secret key

# Serializer for generating tokens
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Connect to SQLite database (create if not exists)
def get_db_connection():
    conn = sqlite3.connect('newsletter.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create users and subscriptions tables
def create_tables():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            subscription_status INTEGER DEFAULT 1 -- 1: Subscribed, 0: Unsubscribed
        )''')
        conn.commit()

# Function to send an unsubscribe email (simulated)
def send_unsubscribe_email(email, token):
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    print(f'Sending unsubscribe link to {email}: {unsubscribe_link}')

# Route to request an unsubscribe link
@app.route('/request_unsubscribe/<int:user_id>')
def request_unsubscribe(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user is None:
        return "User not found", 404

    # Generate a secure token for the user
    token = serializer.dumps(user['email'], salt='unsubscribe-salt')
    send_unsubscribe_email(user['email'], token)
    return "Unsubscribe link sent to your email", 200

# Route for unsubscribe link
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    try:
        # Decode the token within a reasonable time (1 hour for example)
        email = serializer.loads(token, salt='unsubscribe-salt', max_age=3600)
    except:
        return "Invalid or expired token", 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if user is None:
        return "User not found", 404

    if request.method == 'POST':
        # Unsubscribe the user and update the database
        conn.execute('UPDATE users SET subscription_status = 0 WHERE email = ?', (email,))
        conn.commit()
        return "You have been unsubscribed", 200

    # Render the unsubscribe confirmation form
    return render_template_string('''
        <form method="post">
            <p>Why are you unsubscribing?</p>
            <textarea name="reason" required></textarea><br><br>
            <button type="submit">Confirm Unsubscribe</button>
        </form>
    ''')

# Function to add test data to the database
def add_test_user(email):
    with get_db_connection() as conn:
        conn.execute('INSERT INTO users (email) VALUES (?)', (email,))
        conn.commit()

if __name__ == '__main__':
    if not os.path.exists('newsletter.db'):
        create_tables()

    # Add a test user
    add_test_user('testuser@example.com')

    app.run(debug=True)
