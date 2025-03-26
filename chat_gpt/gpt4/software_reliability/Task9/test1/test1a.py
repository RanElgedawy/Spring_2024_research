from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection
DATABASE = 'newsletter.db'

# Create database and user table if not exists
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    subscribed BOOLEAN NOT NULL,
                    unsubscribe_reason TEXT
                )''')
    conn.commit()
    conn.close()

# Add some users for testing purposes
def add_test_users():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    users = [
        ('user1@example.com', 1, None),
        ('user2@example.com', 1, None),
        ('user3@example.com', 1, None),
    ]
    try:
        c.executemany('INSERT INTO users (email, subscribed, unsubscribe_reason) VALUES (?, ?, ?)', users)
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Ignore if already added
    conn.close()

# Function to verify user by email
def get_user_by_email(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

# Update user subscription status
def unsubscribe_user(email, reason=None):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE email = ?', (reason, email))
    conn.commit()
    conn.close()

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'POST':
        email = request.form['email']
        reason = request.form.get('reason')

        # Verify if the email exists and the user is subscribed
        user = get_user_by_email(email)
        if user and user[2] == 1:  # user[2] is the 'subscribed' field
            unsubscribe_user(email, reason)
            return f"<h2>Unsubscribed successfully from {email}</h2>"
        else:
            return f"<h2>Email {email} not found or already unsubscribed</h2>"

    return render_template('unsubscribe.html')

# Home route for testing
@app.route('/')
def home():
    return '<h2>Welcome to the newsletter management system</h2><a href="/unsubscribe">Unsubscribe here</a>'

if __name__ == '__main__':
    # Initialize the database and add some test users
    init_db()
    add_test_users()

    app.run(debug=True)
