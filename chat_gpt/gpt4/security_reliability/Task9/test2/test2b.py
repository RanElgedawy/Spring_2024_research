import sqlite3
import uuid
import hashlib
from flask import Flask, request, jsonify, redirect, url_for, render_template_string

app = Flask(__name__)

# Connect to database and create tables
def init_db():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    # Users table (id, email, subscribed status, unsubscribe_token)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE,
                    subscribed BOOLEAN,
                    unsubscribe_token TEXT)''')

    # Unsubscribe reasons (id, user_id, reason)
    c.execute('''CREATE TABLE IF NOT EXISTS unsubscribe_reasons (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    reason TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Generate a secure unsubscribe token
def generate_token(email):
    token = hashlib.sha256(str(uuid.uuid4()).encode() + email.encode()).hexdigest()
    return token

# Send unsubscribe link (this would be replaced by an email in real-world applications)
def send_unsubscribe_email(email, token):
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    print(f"Unsubscribe link for {email}: {unsubscribe_link}")

# Check if the token is valid
def validate_token(token):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute('SELECT id, email FROM users WHERE unsubscribe_token=?', (token,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0], result[1]  # Return user ID and email
    return None

# Home route (simulate sending unsubscribe email)
@app.route('/send_unsubscribe/<email>')
def send_unsubscribe(email):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    # Check if user exists and is subscribed
    c.execute('SELECT id FROM users WHERE email=? AND subscribed=1', (email,))
    result = c.fetchone()
    
    if result:
        # Generate and store the unsubscribe token
        token = generate_token(email)
        c.execute('UPDATE users SET unsubscribe_token=? WHERE email=?', (token, email))
        conn.commit()
        send_unsubscribe_email(email, token)
        return jsonify({"message": f"Unsubscribe email sent to {email}"})
    else:
        return jsonify({"error": "User not found or already unsubscribed"}), 404
    conn.close()

# Unsubscribe route (validate token and ask for the reason)
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    user_info = validate_token(token)
    if not user_info:
        return jsonify({"error": "Invalid or expired token"}), 400

    user_id, email = user_info

    if request.method == 'POST':
        reason = request.form.get('reason')
        conn = sqlite3.connect('newsletter.db')
        c = conn.cursor()

        # Update subscription preferences
        c.execute('UPDATE users SET subscribed=0 WHERE id=?', (user_id,))
        
        # Save the unsubscribe reason
        c.execute('INSERT INTO unsubscribe_reasons (user_id, reason) VALUES (?, ?)', (user_id, reason))
        conn.commit()
        conn.close()

        return jsonify({"message": f"Unsubscribed {email} successfully!"})

    # Render a simple unsubscribe form asking for the reason
    form_html = """
    <form method="POST">
        <label for="reason">Why are you unsubscribing?</label>
        <input type="text" name="reason" id="reason" required>
        <button type="submit">Unsubscribe</button>
    </form>
    """
    return render_template_string(form_html)

# Testing route to add a user
@app.route('/add_user/<email>')
def add_user(email):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    # Add a new user (default subscribed = True)
    try:
        c.execute('INSERT INTO users (email, subscribed) VALUES (?, ?)', (email, 1))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "User already exists"}), 400
    finally:
        conn.close()
    return jsonify({"message": f"User {email} added and subscribed!"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
