from flask import Flask, request, jsonify
import sqlite3
import hashlib
import urllib.parse
from flask import render_template

app = Flask(__name__)

SECRET_KEY = 'your_secret_key_here'

def generate_unsubscribe_link(email):
    # Combine email and secret key to generate a unique token
    token = hashlib.sha256((email + SECRET_KEY).encode()).hexdigest()
    # Construct the unsubscribe link with the token as a query parameter
    unsubscribe_link = f"http://localhost:5000/unsubscribe?email={urllib.parse.quote(email)}&token={token}"
    return unsubscribe_link

# Database initialization
conn = sqlite3.connect('newsletter_subscriptions.db')
cursor = conn.cursor()

# To prevent from conflicting with preexisting tables.
cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
cursor.execute('''CREATE TABLE IF NOT EXISTS newsletter_subscriptions
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   email TEXT UNIQUE,
                   subscribed BOOLEAN)''')
cursor.execute("INSERT INTO newsletter_subscriptions VALUES (?, ?, ?)", (1, "test@gmail.com", True))
conn.commit()

@app.route('/unsubscribe', methods=['GET'])
def unsubscribe_page():
    email = request.args.get('email')
    if email:
        unsubscribe_link = generate_unsubscribe_link(email)
        print("Unsubscribe link: ", unsubscribe_link)
        return render_template('unsubscribe.html', email=email, unsubscribe_link=unsubscribe_link)
    else:
        return "Invalid unsubscribe link."

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form.get('email')
    token = request.form.get('token')
    reason = request.form.get('reason', '')  # Optional reason for unsubscription

    # Check if the user is logged in (you can implement your authentication logic here)
    # For simplicity, let's assume the user is already logged in

    # Verify the token to ensure the validity of the unsubscribe link
    expected_token = hashlib.sha256((email + SECRET_KEY).encode()).hexdigest()
    if token != expected_token:
        return jsonify({'success': False, 'message': 'Invalid unsubscribe link.'}), 400

    # Verify the user's identity by checking if their email exists in the database
    cursor.execute('SELECT * FROM newsletter_subscriptions WHERE email = ?', (email,))
    user = cursor.fetchone()

    if user:
        # Update the subscription status
        cursor.execute('UPDATE newsletter_subscriptions SET subscribed = ? WHERE email = ?', (False, email))
        conn.commit()
        return jsonify({'success': True, 'message': 'Unsubscribed successfully.', 'reason': reason}), 200
    else:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    # Update the boolean value in the newsletter table for all users
    cursor.execute('UPDATE newsletter_subscriptions SET subscribed = ?', (False,))
    conn.commit()
    return jsonify({'success': True, 'message': 'All users unsubscribed successfully.'}), 200

if __name__ == '__main__':
    app.run(debug=True)