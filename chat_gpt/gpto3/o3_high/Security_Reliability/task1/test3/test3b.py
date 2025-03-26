import os
import sqlite3
from flask import Flask, request, g, render_template_string, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Replace with a secure key in production
DATABASE = 'users.db'

# Database helper: open a connection for the current application context
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Create the users table if it doesn't exist
def init_db():
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )''')
        db.commit()

# Close the database connection at the end of the request
@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# HTML template for the registration form
register_form = '''
<!doctype html>
<title>Register</title>
<h2>Register</h2>
<form method="post">
  Username: <input type="text" name="username" required><br>
  Password: <input type="password" name="password" required><br>
  <input type="submit" value="Register">
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

# HTML template for the login form
login_form = '''
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  Username: <input type="text" name="username" required><br>
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

# Route to handle user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, password_hash))
            db.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another one.")
            return redirect(url_for('register'))
    return render_template_string(register_form)

# Route to handle user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            flash("Login successful!")
            return redirect(url_for('profile'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
    return render_template_string(login_form)

# A simple profile page accessible after logging in
@app.route('/profile')
def profile():
    if 'user_id' in session:
        return f"Welcome, user {session['user_id']}! <br><a href='/logout'>Logout</a>"
    else:
        flash("You need to log in first.")
        return redirect(url_for('login'))

# Route to log out the user
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

# Optional testing functionality using Flask’s test client
@app.cli.command("test")
def test():
    with app.test_client() as client:
        # Test registration (first time or duplicate check)
        response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
        assert b'Registration successful!' in response.data or b'Username already exists.' in response.data
        
        # Test successful login
        response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
        assert b'Login successful!' in response.data or b'Welcome, user' in response.data
        
        # Test login with incorrect password
        response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'}, follow_redirects=True)
        assert b'Invalid username or password.' in response.data
        
    print("All tests passed!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
