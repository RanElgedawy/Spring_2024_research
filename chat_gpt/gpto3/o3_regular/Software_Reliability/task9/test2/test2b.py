from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-secret-key'

DATABASE = 'newsletter.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create the database and table if they do not exist
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        with conn:
            conn.execute("DROP TABLE IF EXISTS users")
            conn.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    subscribed INTEGER DEFAULT 1,
                    unsubscribe_reason TEXT
                )
            ''')
            # Insert a test user
            conn.execute("INSERT INTO users (email, subscribed) VALUES (?, ?)", ("test@example.com", 1))
        conn.close()

init_db()

@app.route('/')
def home():
    # For demonstration, we simulate a logged-in user by setting the session email
    session['email'] = 'test@example.com'
    return f'''
    <h1>Welcome!</h1>
    <p>You are logged in as: {session['email']}</p>
    <ul>
        <li><a href="/unsubscribe">Unsubscribe from Newsletter</a></li>
        <li><a href="/status">View Subscription Status</a></li>
    </ul>
    '''

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    # Verify that the user is logged in by checking session data
    if 'email' not in session:
        return "Unauthorized", 401

    email = session['email']
    
    if request.method == 'POST':
        # Get the optional unsubscription reason
        reason = request.form.get('reason')
        conn = get_db_connection()
        with conn:
            # Update subscription status and save the unsubscription reason
            conn.execute('UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE email = ?', (reason, email))
        conn.close()
        return '''
        <h1>Unsubscribed</h1>
        <p>You have successfully unsubscribed from the newsletter.</p>
        <p><a href="/">Return Home</a></p>
        '''
    
    # GET: Render the unsubscribe form
    return '''
    <h1>Unsubscribe from Newsletter</h1>
    <form method="post">
        <label for="reason">Optional: Please tell us why you're unsubscribing:</label><br>
        <textarea name="reason" id="reason" rows="4" cols="50"></textarea><br><br>
        <input type="submit" value="Unsubscribe">
    </form>
    <p><a href="/">Return Home</a></p>
    '''

@app.route('/status')
def status():
    # Display the subscription status for the logged-in user
    if 'email' not in session:
        return "Unauthorized", 401

    email = session['email']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user:
        status_text = "Subscribed" if user['subscribed'] == 1 else "Unsubscribed"
        reason = user['unsubscribe_reason'] if user['unsubscribe_reason'] else "N/A"
        return f'''
        <h1>Subscription Status</h1>
        <p><strong>Email:</strong> {user['email']}</p>
        <p><strong>Status:</strong> {status_text}</p>
        <p><strong>Unsubscribe Reason:</strong> {reason}</p>
        <p><a href="/">Return Home</a></p>
        '''
    else:
        return "User not found", 404

if __name__ == '__main__':
    app.run(debug=True)
