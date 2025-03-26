from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'  # Needed for session management

DATABASE = 'newsletter.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # So rows can be accessed as dictionaries
    return conn

def init_db():
    """Initializes the database and creates the newsletter_subscribers table if it does not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscribers")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            email TEXT PRIMARY KEY,
            subscribed INTEGER NOT NULL,
            unsubscription_reason TEXT
        )
    ''')
    # For testing, insert a dummy user if not already present.
    test_email = 'test@example.com'
    cursor.execute('SELECT * FROM newsletter_subscribers WHERE email = ?', (test_email,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO newsletter_subscribers (email, subscribed) VALUES (?, ?)', (test_email, 1))
    conn.commit()
    conn.close()

@app.before_first_request
def initialize():
    init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    A dummy login route for testing. In a real application, you would verify credentials.
    This route simply sets the session email.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        session['user_email'] = email
        flash(f'Logged in as {email}')
        return redirect(url_for('unsubscribe'))
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            <label>Email:</label>
            <input type="email" name="email" required>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """
    Unsubscribe route: 
      - Verifies that the user is logged in (via session).
      - Checks that the user exists in the newsletter_subscribers table.
      - Allows the user to optionally provide a reason and then updates the DB.
    """
    if 'user_email' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    user_email = session['user_email']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify that the user exists in the newsletter subscription list
    cursor.execute('SELECT * FROM newsletter_subscribers WHERE email = ?', (user_email,))
    user = cursor.fetchone()
    if not user:
        flash('User not found in subscription list. Please register first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        reason = request.form.get('reason', '')
        # Update the user's subscription status to unsubscribed (0) and save the reason.
        cursor.execute('''
            UPDATE newsletter_subscribers 
            SET subscribed = 0, unsubscription_reason = ?
            WHERE email = ?
        ''', (reason, user_email))
        conn.commit()
        conn.close()
        flash('You have been unsubscribed successfully.')
        return redirect(url_for('unsubscribe_confirmation'))

    conn.close()
    return render_template_string('''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="POST">
            <label>Optional: Provide a reason for unsubscribing:</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br><br>
            <input type="submit" value="Unsubscribe">
        </form>
    ''')

@app.route('/unsubscribe_confirmation')
def unsubscribe_confirmation():
    """Confirmation page after a user has unsubscribed."""
    return render_template_string('''
        <h2>You have been unsubscribed from the newsletter.</h2>
        <a href="{{ url_for('login') }}">Log in with a different email</a>
    ''')

@app.route('/status')
def status():
    """
    A simple status view for testing which displays all users in the newsletter_subscribers table 
    along with their subscription status and any provided unsubscription reason.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM newsletter_subscribers')
    users = cursor.fetchall()
    conn.close()
    response = '<h2>Newsletter Subscription Status</h2><ul>'
    for user in users:
        status_text = 'Subscribed' if user['subscribed'] == 1 else 'Unsubscribed'
        response += f"<li>{user['email']} - {status_text}"
        if user['unsubscription_reason']:
            response += f" (Reason: {user['unsubscription_reason']})"
        response += "</li>"
    response += '</ul>'
    return response

if __name__ == '__main__':
    # Run the app in debug mode for testing.
    app.run(debug=True)
