from flask import Flask, request, render_template
import sqlite3
import secrets

app = Flask(__name__)

# Function to generate a unique token for unsubscribe link
def generate_token():
    return secrets.token_urlsafe(16)

# Insert test data into the database
def insert_test_data():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, subscribed INTEGER, unsubscribe_token TEXT)''')
    test_emails = ['test1@example.com', 'test2@example.com', 'test3@example.com']
    for email in test_emails:
        token = generate_token()
        c.execute('INSERT INTO users (email, subscribed, unsubscribe_token) VALUES (?, ?, ?)', (email, 1, token))
    conn.commit()
    conn.close()

# Initialize test data insertion
insert_test_data()

# Route to provide the unsubscribe link for testing
@app.route('/get_unsubscribe_link/<email>', methods=['GET'])
def get_unsubscribe_link(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Check if email exists in the database
    c.execute('SELECT unsubscribe_token FROM users WHERE email=?', (email,))
    token = c.fetchone()
    conn.close()
    if token:
        unsubscribe_link = f"http://localhost:5000/unsubscribe/{token[0]}"
        return f"Unsubscribe link for {email}: {unsubscribe_link}"
    else:
        return "Email not found in our records."

# Route to handle sending unsubscribe link via email
@app.route('/send_unsubscribe_link', methods=['POST'])
def send_unsubscribe_link():
    email = request.form['email']
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Check if email exists in the database
    c.execute('SELECT unsubscribe_token FROM users WHERE email=?', (email,))
    token = c.fetchone()
    conn.close()
    if token:
        # Send email with unsubscribe link
        # Implementation of sending email omitted for brevity
        return "Unsubscribe link sent to your email."
    else:
        return "Email not found in our records."

# Route to handle user unsubscribing
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    if request.method == 'GET':
        # Check if token is valid
        c.execute('SELECT id FROM users WHERE unsubscribe_token=?', (token,))
        user = c.fetchone()
        if user:
            return """
                <form action="/unsubscribe/{}" method="post">
                    <p>Why are you unsubscribing?</p>
                    <input type="text" name="reason">
                    <input type="submit" value="Unsubscribe">
                </form>
                """.format(token)
        else:
            return "Invalid unsubscribe link."
    elif request.method == 'POST':
        reason = request.form['reason']
        # Update user's subscription status in the database
        c.execute('UPDATE users SET subscribed=0 WHERE unsubscribe_token=?', (token,))
        conn.commit()
        conn.close()
        return "You have been unsubscribed. Reason: {}".format(reason)

# Route to render the unsubscribe all page
@app.route('/unsubscribe_all_page', methods=['GET'])
def unsubscribe_all_page():
    return render_template('unsubscribe_all.html')

# Route to handle unsubscribing all users
@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Update all users' subscription status in the database
    c.execute('UPDATE users SET subscribed=0')
    conn.commit()
    conn.close()
    return "All users have been unsubscribed from the newsletter."

if __name__ == '__main__':
    app.run(debug=True)