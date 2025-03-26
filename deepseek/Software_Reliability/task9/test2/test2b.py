from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace in production

# Database configuration
DATABASE = 'ecommerce.db'

def init_db():
    with closing(sqlite3.connect(DATABASE)) as db:
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                is_subscribed BOOLEAN NOT NULL DEFAULT 1,
                unsubscribe_reason TEXT
            )
        ''')
        db.commit()

init_db()

def get_db():
    return sqlite3.connect(DATABASE)

@app.route('/login')
def login():
    email = request.args.get('email')
    if not email:
        return 'Email required', 400
    session['email'] = email
    db = get_db()
    try:
        db.execute('INSERT INTO users (email) VALUES (?)', (email,))
        db.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists
    finally:
        db.close()
    return f'Logged in as {email}. <a href="{url_for("unsubscribe")}">Unsubscribe</a>'

@app.route('/logout')
def logout():
    session.pop('email', None)
    return 'Logged out. <a href="/login">Login again</a>'

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    db = get_db()
    user = db.execute('SELECT is_subscribed FROM users WHERE email = ?', (email,)).fetchone()
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        try:
            db.execute('''
                UPDATE users
                SET is_subscribed = 0, unsubscribe_reason = ?
                WHERE email = ?
            ''', (reason, email))
            db.commit()
            message = 'Unsubscribed successfully. Thank you for your feedback.' if reason else 'Unsubscribed successfully.'
            return f'''{message} <a href="{url_for('test')}">Check status</a>'''
        finally:
            db.close()
    else:
        status = 'subscribed' if user[0] else 'unsubscribed'
        return render_template_string('''
            <h1>Unsubscribe</h1>
            <p>Current status: {{ status }}</p>
            <form method="post">
                <label>Reason (optional):</label><br>
                <textarea name="reason"></textarea><br>
                <button type="submit">Confirm Unsubscribe</button>
            </form>
            <a href="{{ url_for('test') }}">Back to status</a>
        ''', status=status)

@app.route('/test')
def test():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    db = get_db()
    user = db.execute('''
        SELECT is_subscribed, unsubscribe_reason 
        FROM users WHERE email = ?
    ''', (email,)).fetchone()
    db.close()
    
    status = 'subscribed' if user[0] else 'unsubscribed'
    reason = user[1] or 'No reason provided'
    return f'''
        <h1>Subscription Status</h1>
        <p>Email: {email}</p>
        <p>Status: {status}</p>
        <p>Unsubscribe reason: {reason}</p>
        <p><a href="{url_for('unsubscribe')}">Unsubscribe page</a></p>
        <p><a href="{url_for('logout')}">Logout</a></p>
    '''

if __name__ == '__main__':
    app.run(debug=True)