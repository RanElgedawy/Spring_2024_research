from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 's3cr3t_key'  # Replace with a secure key in production

DATABASE = 'newsletter.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Remove existing database for testing purposes
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    conn = get_db()
    cur = conn.cursor()
    # Create a simple users table
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS subscriptions")
    
    cur.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    # Create a subscriptions table linked to users
    cur.execute('''
        CREATE TABLE subscriptions (
            user_id INTEGER PRIMARY KEY,
            subscribed INTEGER NOT NULL,
            unsubscribe_reason TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Insert a test user and subscription record
    cur.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                ("testuser", "password", "test@example.com"))
    user_id = cur.lastrowid
    cur.execute("INSERT INTO subscriptions (user_id, subscribed, unsubscribe_reason) VALUES (?, ?, ?)",
                (user_id, 1, ""))
    conn.commit()
    conn.close()

# Initialize the database automatically
init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return (f"Logged in as {session['username']}. <a href='/logout'>Logout</a><br>"
                f"<a href='/send_unsubscribe_email'>Send unsubscribe email</a><br>"
                f"<a href='/status'>Check subscription status</a>")
    else:
        return "You are not logged in. <a href='/login'>Login</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>"
    return '''
    <h2>Login</h2>
    <form method="post">
        Username: <input type="text" name="username" required><br>
        Password: <input type="password" name="password" required><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/send_unsubscribe_email')
def send_unsubscribe_email():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    # Generate a secure unsubscribe link (in production, consider using a token)
    unsubscribe_link = url_for('unsubscribe', user_id=user_id, _external=True)
    # Instead of sending an email, we simulate by showing the link
    return (f"Simulated email sent to {session['username']}!<br>"
            f"Click <a href='{unsubscribe_link}'>here</a> to unsubscribe.")

@app.route('/unsubscribe/<int:user_id>', methods=['GET', 'POST'])
def unsubscribe(user_id):
    # Only allow logged in users to proceed
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Prevent a logged in user from unsubscribing another user's account
    if session['user_id'] != user_id:
        return "Error: You are not authorized to unsubscribe this account."
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE subscriptions SET subscribed=0, unsubscribe_reason=? WHERE user_id=?",
                    (reason, user_id))
        conn.commit()
        conn.close()
        return "You have been unsubscribed. Thank you for your feedback!"
    
    # Display a form asking for the reason for unsubscribing
    unsubscribe_form = '''
    <h2>Unsubscribe</h2>
    <form method="post">
        <label>Why are you unsubscribing?</label><br>
        <textarea name="reason" rows="4" cols="50" required></textarea><br>
        <input type="submit" value="Unsubscribe">
    </form>
    '''
    return unsubscribe_form

@app.route('/status')
def status():
    # Endpoint to check the current subscription status (for testing purposes)
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriptions WHERE user_id=?", (user_id,))
    sub = cur.fetchone()
    conn.close()
    if sub:
        status = "Subscribed" if sub['subscribed'] else "Unsubscribed"
        return f"Subscription status: {status}.<br>Unsubscribe reason: {sub['unsubscribe_reason']}"
    return "No subscription record found."

if __name__ == '__main__':
    app.run(debug=True)
