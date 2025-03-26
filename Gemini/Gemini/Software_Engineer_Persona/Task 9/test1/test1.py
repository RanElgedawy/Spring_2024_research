from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import secrets

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS subscribers")
    c.execute("DROP TABLE IF EXISTS newsletter_users")

    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 subscribed BOOLEAN DEFAULT 1,
                 unsubscribe_token TEXT,
                 unsubscribe_reason TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS newsletter_users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 subscribed BOOLEAN DEFAULT 1
                 )''')
    
        # Add test users
    test_users = [
        ("user1@example.com", True),
        ("user2@example.com", True),
        ("user3@example.com", False)
    ]
    c.executemany('''INSERT INTO subscribers (email, subscribed) VALUES (?, ?)''', test_users)
    test_users = [
        ("user1@example.com", True),
        ("user2@example.com", True),
        ("user3@example.com", False)
    ]
    c.executemany('''INSERT INTO newsletter_users (email, subscribed) VALUES (?, ?)''', test_users)

    conn.commit()
    conn.close()

def generate_unique_token():
    return secrets.token_urlsafe(32)

def print_unsubscribe_link(email, unsubscribe_link):
    print(f"Unsubscribe link sent to {email}: {unsubscribe_link}")

@app.route('/generate_unsubscribe_link/<email>')
def generate_unsubscribe_link(email):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM subscribers WHERE email = ?''', (email,))
    subscriber = c.fetchone()

    if subscriber:
        token = subscriber[3]
        if not token:
            token = generate_unique_token()
            c.execute('''UPDATE subscribers SET unsubscribe_token = ? WHERE id = ?''', (token, subscriber[0]))
            conn.commit()

        unsubscribe_link = url_for('unsubscribe_confirm', token=token)
        print(f"Unsubscribe link for {email}: {unsubscribe_link}")
        return "Unsubscribe link generated."
    else:
        return "Email not found."

@app.route('/unsubscribe/confirm/<token>')
def unsubscribe_confirm(token):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM subscribers WHERE unsubscribe_token = ?''', (token,))
    subscriber = c.fetchone()

    if subscriber:
        # Unsubscribe the user
        c.execute('''UPDATE subscribers SET subscribed = 0 WHERE id = ?''', (subscriber[0],))
        conn.commit()

        return render_template('unsubscribe_confirmed.html')
    else:
        # Handle the case where the token is invalid
        return render_template('unsubscribe_failed.html')

@app.route('/unsubscribe_all')
def unsubscribe_all():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute('''UPDATE newsletter_users SET subscribed = 0''')
    conn.commit()
    conn.close()

    return "All users unsubscribed."

if __name__ == '__main__':
    init_db()
    app.run(debug=True)