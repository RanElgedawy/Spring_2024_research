from flask import Flask, request, jsonify, g
import sqlite3

# Configuration
DATABASE = './newsletter.db'
app = Flask(__name__)

# Database setup functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")

        # Create users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            email TEXT UNIQUE,
                            is_subscribed BOOLEAN,
                            reason TEXT
                        )''')
        # Insert a mock user for testing
        cursor.execute('''INSERT OR IGNORE INTO users (email, is_subscribed, reason) 
                          VALUES ('testuser@example.com', 1, NULL)''')
        db.commit()

# Close the DB connection after request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# API endpoint for unsubscribing from the newsletter
@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    # Simulating user authentication: retrieve the user email
    email = request.json.get('email')
    reason = request.json.get('reason', None)

    # Check if the user exists
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if user:
        # Unsubscribe the user and optionally store the reason
        cursor.execute('''UPDATE users SET is_subscribed = 0, reason = ? WHERE email = ?''', (reason, email))
        db.commit()
        return jsonify({"message": f"{email} has been unsubscribed.", "reason": reason}), 200
    else:
        return jsonify({"error": "User not found."}), 404

# Route to simulate a user session (for testing purposes)
@app.route('/test', methods=['GET'])
def test():
    # Simulating a logged-in user who wants to unsubscribe
    mock_email = "testuser@example.com"
    reason = "Too many emails."
    
    # Test the unsubscribe functionality by sending a POST request
    return jsonify({
        "email": mock_email,
        "message": "Unsubscription request sent.",
        "test_unsubscribe": unsubscribe().get_json()
    })

# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(debug=True)
