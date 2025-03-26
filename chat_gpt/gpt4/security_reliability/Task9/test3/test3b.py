from flask import Flask, request, redirect, url_for, render_template, flash
import sqlite3
import hashlib
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a more secure key

# Database setup
DATABASE = 'newsletter.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        is_subscribed INTEGER DEFAULT 1
    )''')

    # Create tokens table to store unsubscribe tokens temporarily
    cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT UNIQUE,
        expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# Function to generate token
def generate_token():
    return hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()

# Email unsubscribe link
def send_unsubscribe_email(email, token):
    sender_email = "your_email@gmail.com"
    receiver_email = email
    password = "your_email_password"  # Use app-specific password if using Gmail
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Unsubscribe from Newsletter"

    body = f"Click the following link to unsubscribe: {unsubscribe_url}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if token exists in the database
    cursor.execute("SELECT user_id FROM tokens WHERE token=?", (token,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]
        if request.method == 'POST':
            reason = request.form.get('reason')
            cursor.execute("UPDATE users SET is_subscribed=0 WHERE id=?", (user_id,))
            conn.commit()

            # Delete token after usage
            cursor.execute("DELETE FROM tokens WHERE token=?", (token,))
            conn.commit()

            flash("You have successfully unsubscribed!", "success")
            return redirect(url_for('index'))
        else:
            return render_template('unsubscribe.html', token=token)
    else:
        flash("Invalid or expired token", "danger")
        return redirect(url_for('index'))

@app.route('/request_unsubscribe/<int:user_id>')
def request_unsubscribe(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if the user exists and is subscribed
    cursor.execute("SELECT email FROM users WHERE id=? AND is_subscribed=1", (user_id,))
    user = cursor.fetchone()

    if user:
        email = user[0]
        token = generate_token()

        # Store the token in the database
        cursor.execute("INSERT INTO tokens (user_id, token) VALUES (?, ?)", (user_id, token))
        conn.commit()

        # Send the unsubscribe email
        if send_unsubscribe_email(email, token):
            flash("Unsubscribe email sent successfully!", "success")
        else:
            flash("Failed to send email.", "danger")
    else:
        flash("User not found or already unsubscribed.", "danger")

    return redirect(url_for('index'))

@app.route('/')
def index():
    return "Welcome to the Newsletter Subscription Service."

# Initialize the database
init_db()

if __name__ == "__main__":
    app.run(debug=True)
