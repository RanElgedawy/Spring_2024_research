from flask import Flask, request, render_template
import sqlite3
import secrets

app = Flask(__name__)

# Function to create database tables if they don't exist
def create_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, subscribed INTEGER, unsubscribe_token TEXT)''')
    conn.commit()
    conn.close()

# Function to generate a unique token for the unsubscribe link
def generate_token():
    return secrets.token_urlsafe(16)

# Function to generate and return the unsubscribe link
def generate_unsubscribe_link(email):
    token = generate_token()
    # Save the token in the database for verification later
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET unsubscribe_token = ? WHERE email = ?", (token, email))
    conn.commit()
    conn.close()
    return token

# Function to send unsubscribe link via terminal
def send_unsubscribe_email(email):
    token = generate_unsubscribe_link(email)
    unsubscribe_link = f"http://127.0.0.1:5000/unsubscribe/{token}"
    print(f"Unsubscribe link for {email}: {unsubscribe_link}")
    return unsubscribe_link

# Route to handle sending the unsubscribe link
@app.route('/send_unsubscribe_link', methods=['POST'])
def send_unsubscribe_link():
    email = request.form['email']
    unsubscribe_link = send_unsubscribe_email(email)
    return f"Unsubscribe link has been generated for {email}: {unsubscribe_link}"

# Route to handle unsubscribe process for individual users
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    if request.method == 'GET':
        # Verify token
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT email FROM users WHERE unsubscribe_token = ?", (token,))
        user = c.fetchone()
        conn.close()
        if user:
            email = user[0]
            return render_template('unsubscribe.html', email=email, token=token)
        else:
            return "Invalid token."
    elif request.method == 'POST':
        reason = request.form['reason']
        # Update subscription preferences in the database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET subscribed = 0 WHERE unsubscribe_token = ?", (token,))
        conn.commit()
        conn.close()
        return "You have been unsubscribed. Thank you for your feedback!"

# Route to handle unsubscribe all process
@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    # Update subscription preferences in the database to unsubscribe all users
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET subscribed = 0")
    conn.commit()
    conn.close()
    return "All users have been unsubscribed from the newsletter."

# Function to insert sample users into the database
def insert_sample_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Insert sample users into the database
    users = [
        ("user1@example.com", 1),
        ("user2@example.com", 1),
        ("user3@example.com", 1)
    ]
    c.executemany("INSERT INTO users (email, subscribed) VALUES (?, ?)", users)
    conn.commit()
    conn.close()

# Test functionality
if __name__ == '__main__':
    create_tables()
    insert_sample_users()
    app.run(debug=True)