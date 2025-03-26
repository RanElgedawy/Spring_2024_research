from flask import Flask, request, jsonify, redirect, url_for, render_template
import sqlite3
import secrets
import urllib.parse

app = Flask(__name__)
app.config['DEBUG'] = False

# Database initialization
def initialize_database():
    conn = sqlite3.connect('newsletter_subscriptions.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            subscribed INTEGER DEFAULT 1
        )
    ''')
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (1, "test@gmail.com", 1))
    conn.commit()
    conn.close()

initialize_database()

# Generate unique unsubscribe link for a user
def generate_unsubscribe_link(email):
    token = secrets.token_urlsafe(16)
    return f"http://localhost:5000/unsubscribe/{urllib.parse.quote(email)}/{token}"

@app.route('/unsubscribe/<email>/<token>', methods=['GET'])
def unsubscribe_with_link(email, token):
    # Verify token
    if email and token:
        conn = sqlite3.connect('newsletter_subscriptions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        if user and request.view_args.get('token') == token:  # Check if the tokens match
            cursor.execute('UPDATE users SET subscribed = 0 WHERE email = ?', (email,))
            conn.commit()
            conn.close()
            return redirect(url_for('reason_for_leaving', email=email))
    return "Error: Invalid Token"

# Page for user to describe reason for leaving
@app.route('/reason_for_leaving', methods=['GET', 'POST'])
def reason_for_leaving():
    if request.method == 'POST':
        email = request.form['email']
        reason = request.form['reason']
        # Here you can do something with the email and reason, like saving them to a database
        return "Thank you for your feedback!"
    else:
        email = request.args.get('email')
        return render_template('reason_for_leaving.html', email=email)

# Function to unsubscribe all users
def unsubscribe_all_users():
    conn = sqlite3.connect('newsletter_subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET subscribed = 0')
    conn.commit()
    conn.close()

# Route for unsubscribing all users
@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    unsubscribe_all_users()
    return "All users unsubscribed successfully."

if __name__ == '__main__':
    unsubscribe_link = generate_unsubscribe_link("test@gmail.com")
    print("Unsubscribe Link:", unsubscribe_link)
    app.run(debug=True)