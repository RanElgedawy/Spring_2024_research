from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session

DATABASE = 'newsletter.db'

# Create and initialize the SQLite database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create users table with subscription status
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                subscribed INTEGER NOT NULL DEFAULT 1,
                reason TEXT
            )
        ''')
        conn.commit()

# Get database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Route to display unsubscribe form
@app.route('/unsubscribe/<email>', methods=['GET'])
def unsubscribe_form(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user is None:
        flash('Invalid email address or user does not exist.', 'error')
        return redirect(url_for('index'))

    return render_template('unsubscribe.html', email=email)

# Route to handle unsubscription
@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form['email']
    reason = request.form.get('reason')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if user:
        conn.execute('UPDATE users SET subscribed = 0, reason = ? WHERE email = ?', (reason, email))
        conn.commit()
        conn.close()
        flash(f'You have successfully unsubscribed from the newsletter.', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('index'))

# Route to display homepage (for testing purposes)
@app.route('/')
def index():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('index.html', users=users)

# Create some initial test users in the database
def seed_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (email, subscribed) VALUES (?, ?)', ('test1@example.com', 1))
        cursor.execute('INSERT OR IGNORE INTO users (email, subscribed) VALUES (?, ?)', ('test2@example.com', 1))
        cursor.execute('INSERT OR IGNORE INTO users (email, subscribed) VALUES (?, ?)', ('test3@example.com', 1))
        conn.commit()

if __name__ == '__main__':
    init_db()  # Initialize the database and tables
    seed_db()  # Seed the database with test data
    app.run(debug=True)
