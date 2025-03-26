from flask import Flask, request, redirect, make_response
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to your own secret key

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
# to prevent conflict with preexisting tables
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        session_id TEXT
    )
''')
cursor.execute("INSERT INTO users (username, password) VALUES (?,?)", ("test", generate_password_hash("pass")))
conn.commit()

# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user[2], password):
            user_obj = User(user[0])
            login_user(user_obj)
            session_id = secrets.token_hex(16)  # Generate a new session ID
            cursor.execute('UPDATE users SET session_id = ? WHERE id = ?', (session_id, user[0]))
            conn.commit()
            resp = make_response(redirect('/'))
            domain = request.host.split(':')[0]  # Remove port if present
            if '.' in domain:
                domain_parts = domain.split('.')
                domain = '.'.join(domain_parts[-2:])  # Get the last two parts for the domain
            resp.set_cookie('session_cookie', session_id, max_age=1800, httponly=True, samesite='Strict', domain=domain, secure=True, path='/')
            return resp
        else:
            return "Invalid username or password"

    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/')
@login_required
def home():
    user_id = current_user.id
    return f'Hello, {user_id}. <a href="/logout">Logout</a>'

@app.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    cursor.execute('UPDATE users SET session_id = NULL WHERE id = ?', (user_id,))
    conn.commit()
    logout_user()
    resp = make_response(redirect('/login'))
    resp.set_cookie('session_cookie', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(debug=True)