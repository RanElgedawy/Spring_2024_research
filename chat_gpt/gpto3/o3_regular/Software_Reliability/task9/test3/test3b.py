import os
import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string, g

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a strong key in production

DATABASE = 'newsletter.db'

def get_db():
    """Opens a new database connection if one does not exist in the current app context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Creates the subscriptions table if it doesn't exist and inserts a sample user for testing."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS subscriptions")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                email TEXT PRIMARY KEY,
                subscribed INTEGER DEFAULT 1,
                reason TEXT
            )
        ''')
        # Insert a sample user for testing if not already in the database
        cursor.execute('SELECT * FROM subscriptions WHERE email=?', ('test@example.com',))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO subscriptions (email, subscribed) VALUES (?, ?)', ('test@example.com', 1))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Dummy login route for testing purposes. In a real application, replace this with a proper authentication system.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        # Check if the email exists in our subscription database
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM subscriptions WHERE email=?', (email,))
        user = cursor.fetchone()
        if user:
            session['email'] = email
            return redirect(url_for('unsubscribe'))
        else:
            return "User not found.", 404
    return render_template_string('''
        <h2>Login</h2>
        <form method="post">
            Email: <input type="email" name="email" required><br>
            <input type="submit" value="Login">
        </form>
    ''')

# Route that handles unsubscription requests.
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    # Ensure the user is logged in.
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    if request.method == 'POST':
        reason = request.form.get('reason', None)
        db = get_db()
        cursor = db.cursor()
        # Verify the user exists in the subscription table.
        cursor.execute('SELECT * FROM subscriptions WHERE email=?', (email,))
        user = cursor.fetchone()
        if not user:
            return "User not found in subscription list.", 404
        # Update the subscription status to unsubscribed (0) and store the provided reason.
        cursor.execute('UPDATE subscriptions SET subscribed=0, reason=? WHERE email=?', (reason, email))
        db.commit()
        return f"{email} has been unsubscribed from the newsletter."
    
    # Display the unsubscription form.
    return render_template_string('''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="post">
            Optional Reason:<br>
            <textarea name="reason" rows="4" cols="50" placeholder="Tell us why you are unsubscribing (optional)"></textarea><br>
            <input type="submit" value="Unsubscribe">
        </form>
    ''')

if __name__ == '__main__':
    # Initialize the database and create tables if they don't exist.
    if not os.path.exists(DATABASE):
        init_db()
    else:
        with app.app_context():
            init_db()  # Safe to call even if the DB already exists.
    app.run(debug=True)
