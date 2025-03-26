from flask import Flask, request, render_template, redirect, url_for, flash
from itsdangerous import URLSafeTimedSerializer
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
serializer = URLSafeTimedSerializer(app.secret_key)

# Connect to or create the database
def init_db():
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (user_id INTEGER PRIMARY KEY, email TEXT UNIQUE, subscribed INTEGER DEFAULT 1, unsubscribe_reason TEXT)''')
    conn.commit()
    conn.close()

# Email sending logic (mockup for now)
def send_unsubscribe_email(user_email, user_id):
    token = serializer.dumps(user_id, salt='unsubscribe-salt')
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    # Here you would send the actual email
    print(f"Unsubscribe link sent to {user_email}: {unsubscribe_url}")

# Route to send unsubscribe link
@app.route('/send_unsubscribe/<int:user_id>')
def send_unsubscribe(user_id):
    # Assuming you have a function to get user email by user_id
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute('SELECT email FROM subscriptions WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        send_unsubscribe_email(user[0], user_id)
        return f"Unsubscribe email sent to {user[0]}"
    else:
        return "User not found", 404

# Unsubscribe link handler
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    try:
        user_id = serializer.loads(token, salt='unsubscribe-salt', max_age=3600)
    except Exception as e:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('error_page'))  # Assume an error page exists

    if request.method == 'POST':
        reason = request.form['reason']
        conn = sqlite3.connect('newsletter.db')
        c = conn.cursor()
        c.execute('UPDATE subscriptions SET subscribed = 0, unsubscribe_reason = ? WHERE user_id = ?', (reason, user_id))
        conn.commit()
        conn.close()
        flash('You have successfully unsubscribed', 'success')
        return redirect(url_for('success_page'))  # Assume a success page exists

    return render_template('unsubscribe.html')  # Render a form asking for the unsubscribe reason

# Testing subscription setup
@app.route('/subscribe/<email>')
def subscribe(email):
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO subscriptions (email, subscribed) VALUES (?, 1)', (email,))
        conn.commit()
        user_id = c.lastrowid
        return f"User with email {email} subscribed with ID {user_id}"
    except sqlite3.IntegrityError:
        return f"User with email {email} already exists."
    finally:
        conn.close()

# Unsubscribe confirmation form (HTML part)
unsubscribe_html = '''
<form method="post">
  <h3>Why are you unsubscribing?</h3>
  <textarea name="reason" rows="4" cols="50" required></textarea><br>
  <input type="submit" value="Unsubscribe">
</form>
'''

# Initialize database when running the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
