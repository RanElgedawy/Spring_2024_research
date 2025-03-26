from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # In production, use a secure secret key

# Database file name
DATABASE = 'newsletter.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create subscriptions table if it doesn't exist
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS subscriptions")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            email TEXT PRIMARY KEY,
            subscribed INTEGER DEFAULT 1,
            unsubscribe_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/')
def index():
    if 'user_email' in session:
        return (f"Logged in as {session['user_email']}<br>"
                f"<a href='/unsubscribe'>Unsubscribe from Newsletter</a><br>"
                f"<a href='/logout'>Logout</a>")
    return "<a href='/login'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        # For testing, we assume any email is valid.
        session['user_email'] = email
        
        # If the user is not yet in the database, create an entry
        conn = get_db_connection()
        cur = conn.execute('SELECT * FROM subscriptions WHERE email = ?', (email,))
        user = cur.fetchone()
        if not user:
            conn.execute('INSERT INTO subscriptions (email, subscribed) VALUES (?, ?)', (email, 1))
            conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Email: <input type="email" name="email" required>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('index'))

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'user_email' not in session:
        flash("You must be logged in to unsubscribe.")
        return redirect(url_for('login'))
    
    email = session['user_email']
    
    if request.method == 'POST':
        # Verify user identity by confirming their email
        confirm_email = request.form['confirm_email']
        if confirm_email != email:
            flash("Email confirmation does not match the logged-in user.")
            return redirect(url_for('unsubscribe'))
        
        # Optional reason for unsubscription
        reason = request.form.get('reason', '')
        conn = get_db_connection()
        conn.execute('UPDATE subscriptions SET subscribed = 0, unsubscribe_reason = ? WHERE email = ?', (reason, email))
        conn.commit()
        conn.close()
        flash("You have successfully unsubscribed from the newsletter.")
        return redirect(url_for('index'))
    
    return render_template_string('''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="POST">
            <!-- Ask the user to confirm their email address -->
            Please confirm your email: <input type="email" name="confirm_email" required value="{{ email }}"><br><br>
            Reason for unsubscription (optional):<br>
            <textarea name="reason" rows="4" cols="50"></textarea><br><br>
            <input type="submit" value="Unsubscribe">
        </form>
    ''', email=email)

if __name__ == '__main__':
    app.run(debug=True)
