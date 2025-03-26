from flask import Flask, request, session, redirect, url_for, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'replace_with_a_secure_random_key'

DATABASE = 'newsletter.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create the newsletter_subscribers table if it doesn't exist.
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscribers")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed INTEGER NOT NULL DEFAULT 1,
            unsubscribed_reason TEXT
        )
    ''')
    # Insert a dummy user for testing if not already present.
    test_email = 'test@example.com'
    cursor.execute("SELECT * FROM newsletter_subscribers WHERE email = ?", (test_email,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO newsletter_subscribers (email, subscribed) VALUES (?, ?)", (test_email, 1))
    db.commit()

@app.before_first_request
def initialize():
    init_db()

# Simple login route for testing.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            session['user_email'] = email
            # If the user doesn't exist in the DB, add them.
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM newsletter_subscribers WHERE email = ?", (email,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO newsletter_subscribers (email, subscribed) VALUES (?, ?)", (email, 1))
                db.commit()
            return redirect(url_for('unsubscribe'))
        else:
            return "Please provide an email.", 400
    return '''
        <h2>Login</h2>
        <form method="post">
            Email: <input type="email" name="email" required>
            <input type="submit" value="Login">
        </form>
    '''

# Unsubscribe route that verifies the logged-in user's identity.
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_email = session['user_email']
    if request.method == 'POST':
        reason = request.form.get('reason')
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE newsletter_subscribers SET subscribed = 0, unsubscribed_reason = ? WHERE email = ?",
            (reason, user_email)
        )
        db.commit()
        return f"User {user_email} has been unsubscribed from the newsletter."
    return '''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="post">
            <label for="reason">Reason for unsubscription (optional):</label><br>
            <textarea name="reason" id="reason" rows="4" cols="50"></textarea><br>
            <input type="submit" value="Unsubscribe">
        </form>
    '''

# A simple status route to check the subscription status (for testing).
@app.route('/status')
def status():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_email = session['user_email']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email, subscribed, unsubscribed_reason FROM newsletter_subscribers WHERE email = ?", (user_email,))
    user = cursor.fetchone()
    if user:
        status_text = "Subscribed" if user[1] else "Unsubscribed"
        return f"Email: {user[0]}<br>Status: {status_text}<br>Reason: {user[2]}"
    else:
        return "User not found.", 404

if __name__ == '__main__':
    app.run(debug=True)
