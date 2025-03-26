from flask import Flask, request, render_template_string, redirect, url_for, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production

DATABASE = 'ecommerce.db'

# Database helper functions
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

def init_db():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS users")
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    db.commit()

# Route for the homepage
@app.route('/')
def index():
    if 'user_id' in session:
        return f"Hello, {session['username']}! Welcome back to our e-commerce platform!"
    return "Welcome to our e-commerce platform! Please <a href='/register'>Register</a> or <a href='/login'>Login</a>."

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username or email already exists!"
    
    return render_template_string('''
        <h2>Register</h2>
        <form method="POST">
            Username: <input type="text" name="username" required><br>
            Email: <input type="email" name="email" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Register">
        </form>
    ''')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        
        if user is None or not check_password_hash(user['password'], password):
            return 'Invalid credentials, please try again!'
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect(url_for('index'))
    
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input type="text" name="username" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
    ''')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Initialize the database before the first request
@app.before_first_request
def initialize():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)