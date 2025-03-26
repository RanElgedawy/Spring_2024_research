import sqlite3
from flask import Flask, request, jsonify

# Create a Flask app
app = Flask(__name__)

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    # Create users and subscriptions table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS subscriptions")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subscribed BOOLEAN NOT NULL DEFAULT 1,
            reason TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Function to insert a user into the database
def add_user(email):
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (email) VALUES (?)', (email,))
        user_id = cursor.lastrowid
        cursor.execute('INSERT INTO subscriptions (user_id, subscribed) VALUES (?, 1)', (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists
    finally:
        conn.close()

# Route to unsubscribe from the newsletter
@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    data = request.json
    email = data.get('email')
    reason = data.get('reason', None)
    
    # Verify that the user exists
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        # Update the subscription status and add the reason if provided
        cursor.execute('''
            UPDATE subscriptions
            SET subscribed = 0, reason = ?
            WHERE user_id = ?
        ''', (reason, user_id))
        conn.commit()
        response = {'message': 'Successfully unsubscribed.'}
    else:
        response = {'error': 'User not found.'}
    
    conn.close()
    return jsonify(response)

# Test the setup by subscribing and unsubscribing users
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email')
    
    # Check if user already exists
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        # Resubscribe the user if they previously unsubscribed
        cursor.execute('UPDATE subscriptions SET subscribed = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        response = {'message': 'Successfully subscribed again.'}
    else:
        add_user(email)
        response = {'message': 'Successfully subscribed.'}
    
    conn.close()
    return jsonify(response)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
