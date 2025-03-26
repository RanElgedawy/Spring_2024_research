from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import sqlite3
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
app.secret_key = 'a_very_secret_key'  # Change this in production!
serializer = URLSafeTimedSerializer(app.secret_key)
DATABASE = 'newsletter.db'

# HTML templates for simplicity
login_template = '''
<!doctype html>
<title>Login</title>
<h1>Login</h1>
<form method="post">
  Email: <input type="text" name="email">
  <input type="submit" value="Login">
</form>
'''

home_template = '''
<!doctype html>
<title>Home</title>
<h1>Home</h1>
{% if 'user_id' in session %}
  <p>Logged in as: {{ session['user_email'] }}</p>
  <a href="{{ url_for('send_unsubscribe_email') }}">Send Unsubscribe Email</a><br>
  <a href="{{ url_for('logout') }}">Logout</a>
{% else %}
  <a href="{{ url_for('login') }}">Login</a>
{% endif %}
'''

unsubscribe_template = '''
<!doctype html>
<title>Unsubscribe</title>
<h1>Unsubscribe</h1>
<p>You are about to unsubscribe from our newsletter.</p>
<form method="post">
  <label for="reason">Please let us know why you're unsubscribing (optional):</label><br>
  <textarea name="reason" rows="4" cols="50"></textarea><br>
  <input type="submit" value="Unsubscribe">
</form>
'''

success_template = '''
<!doctype html>
<title>Success</title>
<h1>Unsubscribed Successfully</h1>
<p>Your subscription preferences have been updated.</p>
'''

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("DROP TABLE IF EXISTS users")
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                subscribed INTEGER DEFAULT 1,
                unsubscribe_reason TEXT
            )
        ''')
    conn.close()

init_db()

# Routes
@app.route('/')
def home():
    return render_template_string(home_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user is None:
            # Create the user if they don't exist
            conn.execute('INSERT INTO users (email) VALUES (?)', (email,))
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        flash('Logged in successfully.')
        return redirect(url_for('home'))
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('home'))

@app.route('/send_unsubscribe_email')
def send_unsubscribe_email():
    if 'user_id' not in session:
        flash('Please log in to send the unsubscribe email.')
        return redirect(url_for('login'))
    # Generate a secure token that includes the user's ID.
    token = serializer.dumps({'user_id': session['user_id']})
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    # In production, you'd email this URL. For testing, it's displayed on the page.
    return f'Unsubscribe link (simulated email): <a href="{unsubscribe_url}">{unsubscribe_url}</a>'

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    token = request.args.get('token')
    if not token:
        return 'Invalid unsubscribe request.', 400
    try:
        data = serializer.loads(token, max_age=3600)  # Token valid for 1 hour
    except SignatureExpired:
        return 'The unsubscribe link has expired.', 400
    except BadSignature:
        return 'Invalid unsubscribe token.', 400

    # Check that the user is logged in
    if 'user_id' not in session:
        flash('Please log in to unsubscribe.')
        return redirect(url_for('login') + f'?next={request.url}')

    # Ensure that the logged-in user matches the token's user_id
    if session['user_id'] != data.get('user_id'):
        return 'Unauthorized access.', 403

    if request.method == 'POST':
        reason = request.form.get('reason', '')
        conn = get_db_connection()
        conn.execute('UPDATE users SET subscribed = 0, unsubscribe_reason = ? WHERE id = ?', (reason, session['user_id']))
        conn.commit()
        conn.close()
        flash('You have been unsubscribed.')
        return render_template_string(success_template)
    return render_template_string(unsubscribe_template)

if __name__ == '__main__':
    app.run(debug=True)
