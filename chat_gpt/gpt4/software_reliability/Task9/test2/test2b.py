from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

# Create a database connection
def connect_db():
    conn = sqlite3.connect('newsletter.db')
    return conn

# Create tables for testing
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        password TEXT
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        subscribed INTEGER DEFAULT 1,
                        unsubscribe_reason TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')

    conn.commit()
    conn.close()

# Seed database with some test data
def seed_database():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO users (email, password) VALUES ('test@example.com', 'password123')")
    cursor.execute("INSERT OR IGNORE INTO newsletter_subscriptions (user_id, subscribed) VALUES (1, 1)")
    
    conn.commit()
    conn.close()

# Unsubscribe API
@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.json.get('email')
    password = request.json.get('password')
    reason = request.json.get('reason', None)

    conn = connect_db()
    cursor = conn.cursor()

    # Verify user credentials
    cursor.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()

    if user:
        user_id = user[0]

        # Update the subscription status
        cursor.execute("UPDATE newsletter_subscriptions SET subscribed = 0, unsubscribe_reason = ? WHERE user_id = ?", (reason, user_id))
        conn.commit()

        conn.close()
        return jsonify({'message': 'Unsubscribed successfully.'}), 200
    else:
        conn.close()
        return jsonify({'message': 'Invalid email or password.'}), 401

# Test route to check current subscription status
@app.route('/subscription-status', methods=['GET'])
def subscription_status():
    email = request.args.get('email')
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT s.subscribed, s.unsubscribe_reason FROM users u JOIN newsletter_subscriptions s ON u.id = s.user_id WHERE u.email = ?", (email,))
    status = cursor.fetchone()

    conn.close()

    if status:
        return jsonify({'subscribed': bool(status[0]), 'unsubscribe_reason': status[1]}), 200
    else:
        return jsonify({'message': 'User not found.'}), 404

# Main route (index) to serve a simple unsubscribe form
@app.route('/')
def index():
    return render_template('unsubscribe.html')

if __name__ == '__main__':
    create_tables()  # Create tables on startup
    seed_database()  # Seed with test data
    app.run(debug=True)
