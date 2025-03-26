import hashlib
import sqlite3
from flask import Flask, render_template, request, redirect, session, g, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'newsletter.db'
SECRET_KEY = 'your_very_secret_key'

# Helper function to get the database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Create the necessary tables in the database
def create_tables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS subscriptions")

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            subscribed INTEGER NOT NULL,
                            subscribed_all INTEGER NOT NULL DEFAULT 1,
                            reason TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(id))''')
        db.commit()

# Dummy data for testing
def insert_dummy_data():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)',
                       ("testuser1@example.com", "password123"))
        cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)',
                       ("testuser2@example.com", "password123"))
        cursor.execute('INSERT INTO subscriptions (user_id, subscribed, subscribed_all) VALUES (?, ?, ?)',
                       (1, 1, 1))  # User 1 is initially subscribed to all
        cursor.execute('INSERT INTO subscriptions (user_id, subscribed, subscribed_all) VALUES (?, ?, ?)',
                       (2, 1, 1))  # User 2 is initially subscribed to all
        db.commit()

# Function to generate a unique unsubscribe token
def generate_unsubscribe_token(user_id):
    token_string = f"{user_id}{SECRET_KEY}"
    return hashlib.sha256(token_string.encode()).hexdigest()

# Function to generate an unsubscribe link
def generate_unsubscribe_link(user_id):
    token = generate_unsubscribe_token(user_id)
    # Manually construct the URL using a formatted string
    unsubscribe_link = f"http://127.0.0.1:5000/unsubscribe/{user_id}/{token}"
    return unsubscribe_link

# Validate the token
def validate_token(user_id, token):
    expected_token = generate_unsubscribe_token(user_id)
    return expected_token == token

# Home route
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return render_template('login.html')

# Profile route to display the unsubscribe link after login
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    unsubscribe_link = generate_unsubscribe_link(user_id)
    return f"Your unsubscribe link is: <a href='{unsubscribe_link}'>{unsubscribe_link}</a>"

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('profile'))
        else:
            return "Invalid login credentials!"
    return render_template('login.html')

# Unsubscribe route with token validation
@app.route('/unsubscribe/<int:user_id>/<token>', methods=['GET'])
def unsubscribe(user_id, token):
    if not validate_token(user_id, token):
        return "Invalid or expired unsubscribe link."

    # Update subscription status
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE subscriptions SET subscribed = 0 WHERE user_id = ?', (user_id,))
    db.commit()
    return "You have successfully unsubscribed from the newsletter."

# Unsubscribe All Users route
@app.route('/unsubscribe_all_users', methods=['POST'])
def unsubscribe_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE subscriptions SET subscribed = 0, subscribed_all = 0')
    db.commit()
    return "All users have been successfully unsubscribed from all newsletters."

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create the tables and insert dummy data when running the script
if __name__ == '__main__':
    create_tables()
    insert_dummy_data()
    app.run(debug=True)