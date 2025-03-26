from flask import Flask, request, jsonify, render_template
import sqlite3
import uuid
import hashlib

app = Flask(__name__)

# Function to generate unique unsubscribe link
def generate_unsubscribe_link(email):
    # Generate a unique token for the unsubscribe link
    token = str(uuid.uuid4())

    # Hash the email and token to make the link more secure
    hash_object = hashlib.sha256(email.encode() + token.encode())
    hashed_link = hash_object.hexdigest()

    # Return the hashed link
    return f"/unsubscribe/{hashed_link}?email={email}"

# Function to unsubscribe all users from newsletter
@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    # Update all users to set subscribed to False
    c.execute("UPDATE users SET subscribed=0")
    conn.commit()

    conn.close()

    return jsonify({'message': 'Successfully unsubscribed all users'}), 200

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 email TEXT UNIQUE,
                 subscribed BOOLEAN)''')
    
    # Data inserted manually for testing purposes
    c.execute("INSERT INTO users (email, subscribed) VALUES (?, ?)", ("test", 1))
    conn.commit()
    conn.close()

# Route to show unsubscribe page
@app.route('/unsubscribe/<hashed_link>', methods=['GET'])
def show_unsubscribe_page(hashed_link):
    email = request.args.get('email')

    # Render a template where the user can provide their reason
    return render_template('unsubscribe.html', hashed_link=hashed_link, email=email)

# Route to handle form submission
@app.route('/unsubscribe/<hashed_link>', methods=['POST'])
def unsubscribe(hashed_link):
    email = request.form.get('email')
    reason = request.form.get('reason')

    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()

    # Update subscription status
    c.execute("UPDATE users SET subscribed=0 WHERE email=?", (email,))
    conn.commit()

    conn.close()

    return jsonify({'message': 'Successfully unsubscribed', 'reason': reason}), 200

# Route to generate unsubscribe link for a user
@app.route('/generate_unsubscribe_link', methods=['GET'])
def get_unsubscribe_link():
    email = request.args.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    hashed_link = generate_unsubscribe_link(email)
    return jsonify({'hashed_link': hashed_link}), 200

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)