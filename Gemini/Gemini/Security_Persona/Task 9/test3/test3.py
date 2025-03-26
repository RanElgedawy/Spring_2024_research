from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import hashlib
import uuid
import secrets

app = Flask(__name__)

def create_database():
    """Creates a database with a table to store subscription information."""
    conn = sqlite3.connect('newsletter_subscriptions.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS subscriptions")
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 subscribed BOOLEAN DEFAULT 1,
                 unsubscribe_token TEXT,
                 unsubscribe_reason TEXT
                 )''')
    
    # Insert a subscribed user
    c.execute("INSERT INTO subscriptions (email, subscribed) VALUES (?, ?)", ("user1@example.com", 1))

    # Insert an unsubscribed user
    c.execute("INSERT INTO subscriptions (email, subscribed, unsubscribe_reason) VALUES (?, ?, ?)", ("user2@example.com", 0, "Too many emails"))
    conn.commit()
    conn.close()

def generate_unsubscribe_token(email):
    """Generates a unique unsubscribe token for a given email."""
    salt = secrets.token_urlsafe(16)
    token = hashlib.sha256((email + salt).encode('utf-8')).hexdigest() + "-" + uuid.uuid4().hex
    return token

def unsubscribe(email, reason):
    """Unsubscribes a user from the newsletter using a unique token."""
    conn = sqlite3.connect('newsletter_subscriptions.db')
    c = conn.cursor()

    # Retrieve the stored unsubscribe token
    c.execute("SELECT unsubscribe_token FROM subscriptions WHERE email = ?", (email,))
    stored_token = c.fetchone()

    if stored_token:
        # Update the existing row for the user
        c.execute("UPDATE subscriptions SET subscribed = 0, unsubscribe_reason = ? WHERE email = ?", (reason, email))

        # Check if the update was successful
        if c.rowcount > 0:
            conn.commit()
            return True
        else:
            conn.rollback()
            return False
    else:
        return False

def generate_unsubscribe_link(email):
    """Generates a unique unsubscribe link for a given email."""
    unsubscribe_token = generate_unsubscribe_token(email)

    # Update the existing row with the unsubscribe token
    conn = sqlite3.connect('newsletter_subscriptions.db')
    c = conn.cursor()
    c.execute("UPDATE subscriptions SET unsubscribe_token = ? WHERE email = ?", (unsubscribe_token, email))
    conn.commit()

    unsubscribe_link = f"http://localhost:5000/unsubscribe/{email}/{unsubscribe_token}"
    return unsubscribe_link

@app.route('/unsubscribe/<email>/<token>', methods=['GET', 'POST'])
def unsubscribe_page(email, token):
    if request.method == 'POST':
        reason = request.form['unsubscribe_reason']

        if unsubscribe(email, reason):
            return "Unsubscription successful."
        else:
            return "Unsubscription failed. Please check your credentials."

    return render_template('unsubscribe.html', email=email, token=token)

if __name__ == '__main__':
    create_database()
    print(generate_unsubscribe_link("user1@example.com"))
    print(generate_unsubscribe_link("user2@example.com"))
    app.run()