from flask import Flask, request, redirect, url_for, render_template_string, session
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with proper secret key in production

# Database setup
DATABASE = 'newsletter.db'

def init_db():
    with closing(sqlite3.connect(DATABASE)) as db:
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                is_subscribed BOOLEAN DEFAULT 1,
                unsubscribe_reason TEXT
            )
        ''')
        # Insert test user if not exists
        try:
            db.execute('INSERT INTO users (email) VALUES (?)', ('test@example.com',))
        except sqlite3.IntegrityError:
            pass
        db.commit()

init_db()

def get_db():
    return sqlite3.connect(DATABASE)

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    # Verify user is logged in (simplified example)
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        
        # Update subscription status
        try:
            db = get_db()
            db.execute('UPDATE users SET is_subscribed = 0, unsubscribe_reason = ? WHERE id = ?',
                      (reason, user_id))
            db.commit()
            return redirect(url_for('unsubscribe_confirmation'))
        except Exception as e:
            return f"Error updating subscription: {str(e)}", 500
    
    # GET request - show unsubscribe form
    return render_template_string('''
        <h2>Unsubscribe from Newsletter</h2>
        <form method="post">
            <label for="reason">Reason for unsubscribing (optional):</label><br>
            <textarea name="reason" rows="4" cols="50"></textarea><br>
            <button type="submit">Unsubscribe</button>
        </form>
    ''')

@app.route('/unsubscribe/confirmation')
def unsubscribe_confirmation():
    return render_template_string('''
        <h2>Unsubscription Successful</h2>
        <p>You have been unsubscribed from our newsletter.</p>
    ''')

# Simplified login system for testing
@app.route('/test/login')
def test_login():
    # Simulate user login - in real system, use proper authentication
    db = get_db()
    user = db.execute('SELECT id FROM users WHERE email = ?', ('test@example.com',)).fetchone()
    if user:
        session['user_id'] = user[0]
        return "Logged in as test@example.com. <a href='/unsubscribe'>Unsubscribe</a>"
    return "Test user not found"

if __name__ == '__main__':
    app.run(debug=True)