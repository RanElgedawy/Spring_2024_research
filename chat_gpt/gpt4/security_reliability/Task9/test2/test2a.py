from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText

# Function to create the necessary tables if they don't exist
def create_tables():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    
    # Create table for users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL,
                    subscription_status TEXT NOT NULL DEFAULT 'subscribed',
                    reason TEXT
                 )''')

    # Create table for tokens
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY,
                    token TEXT NOT NULL,
                    user_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                 )''')
    
    conn.commit()
    conn.close()

# Run this function to ensure tables are created
create_tables()

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set this to a strong secret key
s = URLSafeTimedSerializer(app.secret_key)


def get_db_connection():
    conn = sqlite3.connect('newsletter.db')
    conn.row_factory = sqlite3.Row
    return conn


# Simulate sending email (In production, use a real SMTP server)
def send_email(to_email, subject, body):
    print(f"Sending email to {to_email} with subject: {subject}")
    print(f"Body: {body}")


@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    try:
        email = s.loads(token, max_age=3600)  # Token is valid for 1 hour
    except Exception as e:
        return "Invalid or expired token", 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if user is None:
        return "User not found", 404

    session['user_email'] = user['email']
    return render_template('unsubscribe_form.html')


@app.route('/process_unsubscribe', methods=['POST'])
def process_unsubscribe():
    if 'user_email' not in session:
        return "Unauthorized", 403

    reason = request.form['reason']
    email = session['user_email']

    conn = get_db_connection()
    conn.execute('UPDATE users SET subscription_status = ?, reason = ? WHERE email = ?', 
                 ('unsubscribed', reason, email))
    conn.commit()
    conn.close()

    session.pop('user_email', None)
    flash('You have successfully unsubscribed.')
    return redirect(url_for('home'))


@app.route('/send_unsubscribe_link', methods=['POST'])
def send_unsubscribe_link():
    email = request.form['email']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user is None:
        return "User not found", 404

    token = s.dumps(email)
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    email_body = f"Click the link to unsubscribe: {unsubscribe_link}"

    send_email(email, "Unsubscribe from Newsletter", email_body)
    return "Unsubscribe email sent", 200


@app.route('/')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)