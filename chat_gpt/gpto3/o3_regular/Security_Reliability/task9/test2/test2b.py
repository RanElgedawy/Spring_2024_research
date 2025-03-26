from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-random-key'

DATABASE = 'newsletter.db'

# --- Database Setup ---
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS unsubscribe_tokens")
        
        # Create a users table with subscription status and unsubscribe reason.
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        subscribed INTEGER DEFAULT 1,
                        unsubscribe_reason TEXT
                    )''')
        # Create an unsubscribe_tokens table to store unique tokens for unsubscribe links.
        c.execute('''CREATE TABLE IF NOT EXISTS unsubscribe_tokens (
                        token TEXT PRIMARY KEY,
                        user_id INTEGER,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
        # Insert a sample user for testing if not exists.
        c.execute("SELECT * FROM users WHERE email=?", ("test@example.com",))
        if not c.fetchone():
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                      ("test@example.com", "testpassword"))
        conn.commit()

init_db()

# --- Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_unsubscribe_token(user_id):
    token = str(uuid.uuid4())
    with get_db_connection() as conn:
        conn.execute("INSERT INTO unsubscribe_tokens (token, user_id) VALUES (?, ?)", (token, user_id))
        conn.commit()
    return token

def get_user_by_id(user_id):
    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return user

# --- Templates ---
login_template = """
<h2>Login</h2>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:red;">
      {% for message in messages %}
        <li>{{message}}</li>
      {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="post">
  Email: <input type="email" name="email" required><br>
  Password: <input type="password" name="password" required><br>
  <button type="submit">Login</button>
</form>
"""

home_template = """
<h2>Welcome {{user['email']}}</h2>
<p>Your subscription status: {{ 'Subscribed' if user['subscribed'] else 'Unsubscribed' }}</p>
{% if user['subscribed'] %}
  <p><a href="{{ url_for('send_unsubscribe_email') }}">Unsubscribe from Newsletter</a></p>
{% else %}
  <p>You are already unsubscribed.</p>
{% endif %}
<p><a href="{{ url_for('logout') }}">Logout</a></p>
"""

unsubscribe_form_template = """
<h2>Unsubscribe</h2>
<p>Please let us know why you are unsubscribing:</p>
<form method="post">
  <textarea name="reason" rows="4" cols="50" placeholder="Enter your reason here" required></textarea><br>
  <button type="submit">Confirm Unsubscribe</button>
</form>
"""

message_template = """
<h2>{{ title }}</h2>
<p>{{ message }}</p>
<p><a href="{{ url_for('home') }}">Return Home</a></p>
"""

# --- Routes ---
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    return render_template_string(home_template, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            flash("Logged in successfully.")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.")
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/send_unsubscribe_email')
def send_unsubscribe_email():
    # Ensure the user is logged in.
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    # Generate a secure unsubscribe token.
    token = generate_unsubscribe_token(user['id'])
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    # In a real application, you would email this link.
    # For testing purposes, we simply display the link.
    return render_template_string(message_template,
                                  title="Unsubscribe Email Sent",
                                  message=f"An unsubscribe email has been sent to {user['email']}. "
                                          f"Click <a href='{unsubscribe_link}'>here</a> to unsubscribe.")

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    # Check that the user is logged in.
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    token = request.args.get('token')
    if not token:
        return render_template_string(message_template,
                                      title="Error",
                                      message="Invalid unsubscribe link.")
    # Verify that the token belongs to the logged in user.
    with get_db_connection() as conn:
        token_entry = conn.execute("SELECT * FROM unsubscribe_tokens WHERE token=?", (token,)).fetchone()
    if not token_entry or token_entry['user_id'] != session['user_id']:
        return render_template_string(message_template,
                                      title="Error",
                                      message="Unauthorized unsubscribe attempt.")
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        # Update subscription preferences in the database.
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET subscribed=0, unsubscribe_reason=? WHERE id=?", (reason, session['user_id']))
            # Optionally remove the token after use.
            conn.execute("DELETE FROM unsubscribe_tokens WHERE token=?", (token,))
            conn.commit()
        return render_template_string(message_template,
                                      title="Unsubscribed",
                                      message="You have been unsubscribed from our newsletter.")
    
    return render_template_string(unsubscribe_form_template)

# --- Test Route ---
@app.route('/reset')
def reset():
    """Reset subscription status for the logged-in user (for testing)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET subscribed=1, unsubscribe_reason=NULL WHERE id=?", (session['user_id'],))
        conn.commit()
    return render_template_string(message_template,
                                  title="Reset",
                                  message="Subscription status has been reset to subscribed.")

if __name__ == '__main__':
    app.run(debug=True)
