from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to a secure key in production

DATABASE = 'newsletter.db'

def init_db():
    """Initialize the SQLite database and create the users table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    # Create table to store user info and subscription status
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT,
                    subscribed INTEGER DEFAULT 1,
                    unsubscribe_reason TEXT
                )''')
    # Insert a test user if one doesn't exist
    c.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@example.com", "password"))
    conn.commit()
    conn.close()

@app.before_first_request
def initialize():
    init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Simple login page; in a production system, add proper password hashing and security measures
@app.route('/login', methods=['GET', 'POST'])
def login():
    html = '''
    <h2>Login</h2>
    <form method="post">
      Email: <input type="email" name="email" required><br>
      Password: <input type="password" name="password" required><br>
      <input type="submit" value="Login">
    </form>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    '''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and user[1] == password:
            session['user_id'] = user[0]
            session['email'] = email
            flash("Logged in successfully.")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.")
    return render_template_string(html)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    html = '''
    <h2>Dashboard</h2>
    <p>Welcome, {{ email }}!</p>
    <p><a href="{{ url_for('send_unsubscribe') }}">Unsubscribe from Newsletter</a></p>
    <p><a href="{{ url_for('logout') }}">Logout</a></p>
    '''
    return render_template_string(html, email=session.get('email'))

# This route simulates sending an unsubscribe email by displaying the unsubscribe link.
@app.route('/send_unsubscribe')
def send_unsubscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Generate an unsubscribe link; here we use the user's id for demonstration.
    unsubscribe_link = url_for('unsubscribe', user_id=session['user_id'], _external=True)
    html = '''
    <h2>Unsubscribe Email Simulation</h2>
    <p>An email has been "sent" to your address with the following link:</p>
    <p><a href="{{ unsubscribe_link }}">{{ unsubscribe_link }}</a></p>
    <p><a href="{{ url_for('dashboard') }}">Back to Dashboard</a></p>
    '''
    return render_template_string(html, unsubscribe_link=unsubscribe_link)

# Unsubscribe route that only allows the logged in user to unsubscribe their own account.
@app.route('/unsubscribe/<int:user_id>', methods=['GET', 'POST'])
def unsubscribe(user_id):
    if 'user_id' not in session:
        flash("You must be logged in to unsubscribe.")
        return redirect(url_for('login', next=request.url))
    # Prevent users from unsubscribing others
    if session['user_id'] != user_id:
        flash("You are not authorized to unsubscribe another user.")
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT subscribed FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        flash("User not found.")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        # Update the user's subscription status and record their reason
        c.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE id = ?", (reason, user_id))
        conn.commit()
        conn.close()
        flash("You have been unsubscribed.")
        return redirect(url_for('dashboard'))
    conn.close()
    html = '''
    <h2>Unsubscribe</h2>
    <form method="post">
      <label>Please let us know why you're unsubscribing (optional):</label><br>
      <textarea name="reason" rows="4" cols="50"></textarea><br>
      <input type="submit" value="Unsubscribe">
    </form>
    <p><a href="{{ url_for('dashboard') }}">Cancel</a></p>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    # Run the app in debug mode; remove debug=True in production
    app.run(debug=True)
