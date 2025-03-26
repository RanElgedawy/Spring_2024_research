from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask import g
from itsdangerous import URLSafeTimedSerializer, BadSignature
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
serializer = URLSafeTimedSerializer(app.secret_key)

# Database setup
DATABASE = './users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def create_user_table():
    with app.app_context():
        db = get_db()
        # Create the table if it doesn't exist
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            subscribed_to_newsletter INTEGER NOT NULL DEFAULT 1
        )
        ''')
        db.commit()

        # Add test data
        insert_test_data()

def insert_test_data():
    db = get_db()
    test_users = [
        ('user1@example.com', 1),
        ('user2@example.com', 1),
        ('user3@example.com', 1)
    ]

    for email, subscribed in test_users:
        try:
            db.execute('INSERT INTO users (email, subscribed_to_newsletter) VALUES (?, ?)', (email, subscribed))
        except sqlite3.IntegrityError:
            # Ignore if the user already exists (for repeated testing)
            pass

    db.commit()


def update_subscription(email, subscribed):
    db = get_db()
    db.execute('UPDATE users SET subscribed_to_newsletter = ? WHERE email = ?', (subscribed, email))
    db.commit()

def get_user_by_email(email):
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cur.fetchone()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Helper functions
def send_unsubscribe_email(user_email):
    token = serializer.dumps(user_email, salt='unsubscribe-salt')
    unsubscribe_link = url_for('unsubscribe', token=token, _external=True)
    print(f"Unsubscribe link for {user_email}: {unsubscribe_link}")
    # In a real application, you'd send this via email

def verify_token(token):
    try:
        email = serializer.loads(token, salt='unsubscribe-salt', max_age=3600)
        return email
    except BadSignature:
        return None

# Routes
@app.route('/')
def index():
    return "Welcome to the newsletter page!"

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    email = verify_token(token)
    if email is None:
        return "Invalid or expired token.", 403

    # Check if the user is logged in and the session email matches the token email
    if 'user_email' not in session or session['user_email'] != email:
        flash("You need to be logged in to unsubscribe.")
        return redirect(url_for('login'))

    # If the user is authenticated, display the unsubscribe form
    user = get_user_by_email(email)
    if request.method == 'POST':
        reason = request.form.get('reason')
        print(f"User {email} unsubscribed for reason: {reason}")
        update_subscription(email, 0)  # Update the user's subscription status
        return f"You have been unsubscribed, {email}."

    return render_template('unsubscribe_form.html', email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user_by_email(email)
        if user:
            session['user_email'] = email
            print(f"User email stored in session: {session['user_email']}")
            flash("You are now logged in!")
            return redirect(url_for('index'))
        else:
            flash("Invalid email. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/send_unsubscribe_link', methods=['POST'])
def send_unsubscribe_link():
    email = request.form.get('email')
    user = get_user_by_email(email)
    if user:
        send_unsubscribe_email(user[1])
        return f"An unsubscribe link has been sent to {email}."
    return "User not found."

def update_newsletter_subscription(email, subscribed_to_newsletter):
    db = get_db()
    db.execute('UPDATE users SET subscribed_to_newsletter = ? WHERE email = ?', 
               (subscribed_to_newsletter, email))
    db.commit()

@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    # Ensure only logged-in users can access this
    if 'user_email' not in session:
        flash("You need to be logged in to perform this action.")
        return redirect(url_for('login'))
    
    # Update all users in the database
    db = get_db()
    db.execute('UPDATE users SET subscribed_to_newsletter = 0')
    db.commit()
    
    flash("All users have been unsubscribed from the newsletter.")
    return redirect(url_for('index'))

@app.route('/debug_session')
def debug_session():
    return str(session)

if __name__ == '__main__':
    # Create the user table if it doesn't exist
    create_user_table()
    
    # Run the Flask app
    app.run(debug=True)