from flask import Flask, request, redirect, url_for, g
import sqlite3
import os

DATABASE = 'newsletter.db'
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Database initialization
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# SQL schema (automatically created if not exists)
schema_sql = """
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS unsubscriptions;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    subscribed BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE unsubscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
"""

with open('schema.sql', 'w') as f:
    f.write(schema_sql)
init_db()

# Helper function to create test user
def create_test_user(email='test@example.com'):
    db = get_db()
    db.execute('INSERT OR IGNORE INTO users (email, subscribed) VALUES (?, ?)', 
              (email, 1))
    db.commit()
    return db.execute('SELECT last_insert_rowid() AS id').fetchone()['id']

# Unsubscribe route
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'POST':
        # In real application, user_id would come from session
        user_id = request.form.get('user_id')
        reason = request.form.get('reason', '')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            return "User not found", 404
            
        if user['subscribed'] == 0:
            return "Already unsubscribed", 400

        # Update subscription status
        db.execute('UPDATE users SET subscribed = 0 WHERE id = ?', (user_id,))
        # Record unsubscription reason
        db.execute('INSERT INTO unsubscriptions (user_id, reason) VALUES (?, ?)',
                  (user_id, reason))
        db.commit()
        return redirect(url_for('unsubscribe_success'))

    # GET request (show unsubscribe form)
    return '''
        <form method="POST">
            <input type="hidden" name="user_id" value="{user_id}">
            <label>Reason for unsubscribing (optional):</label>
            <textarea name="reason"></textarea>
            <button type="submit">Unsubscribe</button>
        </form>
    '''

@app.route('/unsubscribe/success')
def unsubscribe_success():
    return "You have been successfully unsubscribed."

# Testing endpoint
@app.route('/test')
def test_unsubscription():
    # Create test user
    test_user_id = create_test_user()
    
    # Simulate unsubscription request
    test_client = app.test_client()
    response = test_client.post('/unsubscribe', data={
        'user_id': test_user_id,
        'reason': 'Testing unsubscription'
    })
    
    # Verify results
    db = get_db()
    user_status = db.execute('SELECT subscribed FROM users WHERE id = ?', 
                            (test_user_id,)).fetchone()[0]
    unsub_record = db.execute('SELECT * FROM unsubscriptions WHERE user_id = ?',
                             (test_user_id,)).fetchone()

    return f'''
        Test Results:<br>
        - Subscription Status: {'Subscribed' if user_status else 'Unsubscribed'}<br>
        - Unsubscription Reason Recorded: {unsub_record['reason'] if unsub_record else 'None'}
    '''

if __name__ == '__main__':
    with app.app_context():
        create_test_user('manualtest@example.com')

    app.run(debug=True)