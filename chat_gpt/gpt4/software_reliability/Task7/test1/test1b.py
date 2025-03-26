from flask import Flask, request, redirect, url_for, render_template, make_response
import sqlite3
import hashlib

app = Flask(__name__)
DATABASE = 'user_data.db'

# Function to create a new database and users table if it does not exist
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL)''')
    # Add a test user (username: user1, password: password123)
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                   ('user1', hashlib.sha256('password123'.encode()).hexdigest()))
    conn.commit()
    conn.close()

# Route to display the login form and handle login submissions
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        # Validate user credentials
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Set cookie for the current domain, restrict to the current domain
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('user_session', username, httponly=True, domain='localhost')
            return response
        else:
            return "Invalid credentials, please try again."
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

# Dashboard route (accessible only if logged in)
@app.route('/dashboard')
def dashboard():
    user_session = request.cookies.get('user_session')
    if user_session:
        return f"Welcome, {user_session}! <br><a href='/logout'>Logout</a>"
    else:
        return redirect(url_for('login'))

# Logout route to clear the cookie
@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('user_session', '', expires=0, domain='localhost')  # Clear the cookie
    return response

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize the database with test data
    init_db()
    # Run the Flask app
    app.run(debug=True)