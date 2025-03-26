from flask import Flask, request, render_template, redirect, url_for
import os
import sqlite3
import hashlib
import secrets
import base64

app = Flask(__name__)

def create_database():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  password TEXT,
                  subscribed BOOLEAN DEFAULT 1,
                  unsubscribe_token TEXT)''')
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password) VALUES ('test@example.com', 'password123')")

    conn.commit()
    conn.close()

def generate_unsubscribe_link(user_id):
    # Generate a random token and encode it
    token = secrets.token_urlsafe(32)
    encoded_token = base64.urlsafe_b64encode(token.encode()).decode()

    # Store the token in the database associated with the user
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute("UPDATE users SET unsubscribe_token=? WHERE id=?", (encoded_token, user_id))
    conn.commit()
    conn.close()

    # Construct the unsubscribe link using localhost during development
    base_url = f"http://{os.environ.get('FLASK_APP_HOST', 'localhost')}:5000"
    unsubscribe_link = f"{base_url}/unsubscribe?token={encoded_token}"
    return unsubscribe_link

def unsubscribe_user_by_token(token):
    # Decode the token and verify it
    decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
    print("Decoded token:", decoded_token)

    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    # Execute the query with the decoded token
    c.execute("SELECT id FROM users WHERE unsubscribe_token=?", (decoded_token,))
    user_id = c.fetchone()

    if user_id:
        print("User ID found:", user_id[0])
        # Update subscription status and remove the token
        c.execute("UPDATE users SET subscribed=0, unsubscribe_token=NULL WHERE id=?", (user_id[0],))
        conn.commit()
        return True
    else:
        print("User ID not found")
        return False

def unsubscribe(email, password, reason=None):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    # Verify user credentials using hashed password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, hashed_password))
    user_id = c.fetchone()

    if user_id:
        # Update subscription status and optionally store reason
        c.execute("UPDATE users SET subscribed=0 WHERE id=?", (user_id[0],))
        if reason:
            c.execute("INSERT INTO unsubscribe_reasons (user_id, reason) VALUES (?, ?)", (user_id[0], reason))
        conn.commit()
        return True
    else:
        return False

def test_unsubscribe():
    # Create test data
    create_database()
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password) VALUES ('test@example.com', 'password123')")
    conn.commit()
    conn.close()

    # Test unsubscription
    result = unsubscribe('test@example.com', 'password123', 'Too many emails')
    print(result)  # Should print True

@app.route('/generate_unsubscribe_link', methods=['GET'])
def generate_unsubscribe_link_test():
    # Assuming you have a way to get the user's ID
    user_id = 1  # Replace with actual user ID

    link = generate_unsubscribe_link(user_id)
    return render_template('unsubscribe_link.html', link=link)

@app.route('/unsubscribe', methods=['GET'])
def unsubscribe_by_token():
    token = request.args.get('token')
    if token:
        decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
        print(f"Received token: {token}")
        print(f"Decoded token: {decoded_token}")

        if unsubscribe_user_by_token(token):
            return render_template('unsubscribe_reason.html')
        else:
            print("Unsubscribe failed")
            return redirect(url_for('unsubscribe_error'))
    else:
        return render_template('unsubscribe_error.html')

@app.route('/unsubscribe_reason', methods=['POST'])
def submit_unsubscribe_reason():
    reason = request.form.get('reason')
    # Store the reason in the database (if needed)
    return redirect(url_for('unsubscribe_success'))

@app.route('/unsubscribe_error')
def unsubscribe_error():
    return render_template('unsubscribe_error.html')

@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    # Get all user IDs
    c.execute("SELECT id FROM users")
    user_ids = c.fetchall()

    for user_id in user_ids:
        # Generate a unique unsubscribe token for each user
        token = generate_unsubscribe_link(user_id[0])

        # Call unsubscribe_by_token with the generated token
        unsubscribe_by_token(token)

    conn.commit()
    conn.close()

    return redirect(url_for('unsubscribe_all_success'))

@app.route('/unsubscribe_all_success')
def unsubscribe_all_success():
    return render_template('unsubscribe_all_success.html')
    
if __name__ == '__main__':
    create_database()
    app.run(debug=True)