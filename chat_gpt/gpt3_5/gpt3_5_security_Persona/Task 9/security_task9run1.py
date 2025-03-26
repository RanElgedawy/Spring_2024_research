from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import secrets

app = Flask(__name__)

# Database initialization
conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, token TEXT, subscribed BOOLEAN)''')
# Insert test users
users = [
    ('user1@example.com', 'token1', True),
    ('user2@example.com', 'token2', True),
    ('user3@example.com', 'token3', True)
]
c.executemany("INSERT INTO users (email, token, subscribed) VALUES (?, ?, ?)", users)
conn.commit()


# Function to generate a unique token
def generate_token():
    return secrets.token_urlsafe(16)

# Function to send unsubscribe email
def send_unsubscribe_email(email, token):
    # In a real application, you would implement code to send the email with the token.
    # For simplicity, we'll just print the token here.
    print("Unsubscribe link: http://localhost:5000/unsubscribe/{}".format(token))

# Route to unsubscribe page
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            return "Email is required", 400
        
        token = generate_token()
        send_unsubscribe_email(email, token)
        
        # Check if the email already exists in the database
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = c.fetchone()
        if existing_user:
            # Update token for existing user
            c.execute("UPDATE users SET token = ? WHERE email = ?", (token, email))
        else:
            # Save new user in the database
            c.execute("INSERT INTO users (email, token, subscribed) VALUES (?, ?, ?)", (email, token, True))
        conn.commit()
        
        return "Unsubscribe link has been sent to your email"
    return render_template('unsubscribe_form.html')

# Route to unsubscribe confirmation page
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def confirm_unsubscribe(token):
    if request.method == 'POST':
        email = request.form.get('email')
        reason = request.form.get('reason')
        
        c.execute("SELECT * FROM users WHERE token = ?", (token,))
        user = c.fetchone()
        if not user:
            return "Invalid token", 400
        
        if user[1] != email:
            return "Email does not match token", 400
        
        c.execute("UPDATE users SET subscribed = 0 WHERE email = ?", (email,))
        conn.commit()
        
        # Remove user from the database after unsubscribing
        c.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        
        return "You have been unsubscribed successfully. Reason: {}".format(reason)
    
    c.execute("SELECT email FROM users WHERE token = ?", (token,))
    user = c.fetchone()
    if not user:
        return "Invalid token", 400
    
    email = user[0]
    return render_template('confirm_unsubscribe.html', email=email, token=token)

# Route to unsubscribe all users
@app.route('/unsubscribe/all', methods=['GET', 'POST'])
def unsubscribe_all():
    if request.method == 'POST':
        c.execute("UPDATE users SET subscribed = 0")
        conn.commit()
        return "All users have been unsubscribed successfully"
    return render_template('unsubscribe_all.html')

if __name__ == '__main__':
    app.run(debug=True)