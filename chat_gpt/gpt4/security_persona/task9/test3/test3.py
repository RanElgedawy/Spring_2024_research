import sqlite3
import uuid
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# Initialize database schema
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS unsubscribe_tokens")
        cursor.execute("DROP TABLE IF EXISTS newsletter")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                subscribed BOOLEAN DEFAULT TRUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscribed BOOLEAN DEFAULT TRUE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unsubscribe_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE,
                expiration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute("INSERT INTO users (email, subscribed) VALUES ('testuser1@example.com', 1)")
        cursor.execute("INSERT INTO users (email, subscribed) VALUES ('testuser2@example.com', 1)")
        cursor.execute("INSERT INTO newsletter (user_id, subscribed) VALUES (1, 1)")

        conn.commit()

init_db()

# Prototype email functionality - printing the unsubscribe link to console
def prototype_send_unsubscribe_email(user_email, token):
    unsubscribe_link = f"http://127.0.0.1:5000/unsubscribe/{token}"
    subject = "Unsubscribe from Newsletter"
    message = f"Subject: {subject}\n\nClick the following link to unsubscribe: {unsubscribe_link}"
    
    # Instead of sending an email, we print the message to the console for testing
    print(f"--- Prototype Email ---\nTo: {user_email}\n{message}\n")

# Route to request an unsubscribe link
@app.route('/request-unsubscribe/<int:user_id>')
def request_unsubscribe(user_id):
    # Validate the user exists and is subscribed
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, subscribed FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if user and user[1]:  # Check if user exists and is subscribed
            token = str(uuid.uuid4())
            cursor.execute('INSERT INTO unsubscribe_tokens (user_id, token) VALUES (?, ?)', (user_id, token))
            conn.commit()
            
            prototype_send_unsubscribe_email(user[0], token)
            return f"An email prototype has been sent to {user[0]} to confirm the unsubscribe request."
        return "User not found or not subscribed", 404

# Route to handle the unsubscribe link
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM unsubscribe_tokens WHERE token = ?', (token,))
        token_data = cursor.fetchone()
        
        if not token_data:
            return "Invalid or expired token.", 400
        
        if request.method == 'POST':
            reason = request.form['reason']
            user_id = token_data[0]
            cursor.execute('UPDATE users SET subscribed = 0 WHERE id = ?', (user_id,))
            cursor.execute('DELETE FROM unsubscribe_tokens WHERE token = ?', (token,))
            conn.commit()
            
            return render_template('confirmation.html', reason=reason)
        
        return render_template('unsubscribe.html', token=token)

# Route to unsubscribe all users from the newsletter (admin functionality)
@app.route('/admin/unsubscribe-all', methods=['POST'])
def unsubscribe_all_users():
    # Unsubscribe all users from the newsletter
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE newsletter SET subscribed = 0')
        conn.commit()

    return "All users have been unsubscribed from the newsletter."

# Admin page to display the "Unsubscribe All" button
@app.route('/admin')
def admin_page():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)