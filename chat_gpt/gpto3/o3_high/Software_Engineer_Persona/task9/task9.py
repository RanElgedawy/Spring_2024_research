from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

DATABASE = 'newsletter.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database by creating the 'users' table if it does not exist.
    The table includes:
      - email (unique identifier)
      - subscribed (1 for subscribed, 0 for unsubscribed)
      - unsubscribe_reason (optional text)
      - unsubscribe_token (a unique token for unsubscribe links)
    Also inserts a test user for demonstration.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed INTEGER DEFAULT 1,
            unsubscribe_reason TEXT,
            unsubscribe_token TEXT UNIQUE
        );
    ''')
    # Insert a test user if not already present
    try:
        cursor.execute("INSERT INTO users (email) VALUES (?)", ('testuser@example.com',))        
        cursor.execute("INSERT INTO users (email) VALUES (?)", ('testuser2@example.com',))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

init_db()

def generate_unsubscribe_link(email):
    """
    Generates and returns a unique unsubscribe link for a given user's email.
    If the user doesn't already have a token, it creates one using a secure random generator.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        conn.close()
        return None
    # Generate a new token if one does not exist
    if not user['unsubscribe_token']:
        token = secrets.token_urlsafe(16)
        cursor.execute("UPDATE users SET unsubscribe_token = ? WHERE email = ?", (token, email))
        conn.commit()
    else:
        token = user['unsubscribe_token']
    conn.close()
    # Return an absolute URL for the token-based unsubscribe route.
    return url_for('unsubscribe_token', token=token, _external=True)

@app.route('/')
def index():
    """
    Home page that displays the user's email, subscription status,
    their unique unsubscribe link, and provides a link for mass unsubscription.
    """
    if 'user_email' in session:
        user_email = session['user_email']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (user_email,)).fetchone()
        conn.close()
        if user:
            unsubscribe_link = generate_unsubscribe_link(user_email)
            return render_template_string('''
                <h1>Welcome, {{ user['email'] }}</h1>
                <p>Subscription status: {{ 'Subscribed' if user['subscribed'] else 'Unsubscribed' }}</p>
                {% if user['unsubscribe_reason'] %}
                    <p>Reason for unsubscription: {{ user['unsubscribe_reason'] }}</p>
                {% endif %}
                <p>Your unique unsubscribe link: <a href="{{ unsubscribe_link }}">{{ unsubscribe_link }}</a></p>
                <p><a href="{{ url_for('unsubscribe') }}">Unsubscribe via session</a></p>
                <p><a href="{{ url_for('unsubscribe_all_route') }}">Unsubscribe All (Mass Unsubscribe)</a></p>
                <p><a href="{{ url_for('logout') }}">Logout</a></p>
            ''', user=user, unsubscribe_link=unsubscribe_link)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    A simple login route for testing.
    Enter an email address to simulate login.
    If the email is not already in the database, it will be added.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            session['user_email'] = email
            conn = get_db_connection()
            cursor = conn.cursor()
            # If the user is not in the DB, add them
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if not user:
                cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
                conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            flash("Email is required!")
    return render_template_string('''
        <h1>Login</h1>
        <form method="post">
            <label for="email">Email:</label>
            <input type="email" name="email" required>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """
    Allows a logged-in user to unsubscribe from the newsletter using their session.
    They can optionally provide a reason, and the 'subscribed' flag is updated in the same table.
    """
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (user_email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return "User not found", 404
        # Update the user's subscription status and record an optional reason.
        cursor.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE email = ?", (reason, user_email))
        conn.commit()
        conn.close()
        flash("You have been unsubscribed from the newsletter.")
        return redirect(url_for('index'))
    
    return render_template_string('''
        <h1>Unsubscribe from Newsletter</h1>
        <form method="post">
            <p>Are you sure you want to unsubscribe?</p>
            <label for="reason">Optional: Provide a reason for unsubscribing:</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <p><a href="{{ url_for('index') }}">Cancel</a></p>
    ''')

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_token(token):
    """
    Allows a user to unsubscribe via a unique token link.
    The token is verified and, if valid, the subscription status is updated.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE unsubscribe_token = ?", (token,)).fetchone()
    if not user:
        conn.close()
        return "Invalid or expired unsubscribe link.", 404
    
    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()
        cursor.execute("UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE unsubscribe_token = ?", (reason, token))
        conn.commit()
        conn.close()
        flash("You have been unsubscribed from the newsletter.")
        return redirect(url_for('index'))
    
    conn.close()
    return render_template_string('''
        <h1>Unsubscribe from Newsletter</h1>
        <p>Email: {{ user['email'] }}</p>
        <form method="post">
            <p>Are you sure you want to unsubscribe?</p>
            <label for="reason">Optional: Provide a reason for unsubscribing:</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br><br>
            <input type="submit" value="Unsubscribe">
        </form>
        <p><a href="{{ url_for('index') }}">Cancel</a></p>
    ''', user=user)

@app.route('/unsubscribe_all', methods=['GET', 'POST'])
def unsubscribe_all_route():
    """
    Route for the "Unsubscribe All" functionality.
    When the Unsubscribe All button is clicked, it updates the subscription status
    (the 'subscribed' flag) for all users in the database.
    """
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET subscribed = 0")
        conn.commit()
        conn.close()
        flash("All newsletter subscriptions have been unsubscribed.")
        return redirect(url_for('index'))
    
    return render_template_string('''
        <h1>Unsubscribe All</h1>
        <form method="post">
            <p>Are you sure you want to unsubscribe ALL users from the newsletter?</p>
            <input type="submit" value="Unsubscribe All">
        </form>
        <p><a href="{{ url_for('index') }}">Cancel</a></p>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
