from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import secrets

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('newsletter.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create database tables if they don't exist
def init_db():
    conn = get_db_connection()
    conn.executescript('''
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS subscriptions;
        
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER,
            subscribed BOOLEAN DEFAULT 1,
            unsubscribe_reason TEXT,
            token TEXT UNIQUE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        # Generate the token
        token = secrets.token_urlsafe(32)

        if existing_user:
            # Update the subscription status if the user is already in the database
            cursor.execute("UPDATE subscriptions SET subscribed = 1 WHERE user_id = ?", (existing_user[0],))
        else:
            # Insert the new user and subscription
            cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO subscriptions (user_id, token) VALUES (?, ?)", (user_id, token))

        conn.commit()

        # Generate the unsubscribe link
        unsubscribe_link = request.url_root + f'/unsubscribe/{token}'

        return render_template('subscribe_success.html', unsubscribe_link=unsubscribe_link)

    return render_template('subscribe_form.html')

@app.route('/unsubscribe/<token>')
def unsubscribe_page(token):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find the user based on the token
    cursor.execute("SELECT user_id FROM subscriptions WHERE token = ?", (token,))
    user_id = cursor.fetchone()

    if user_id:
        return render_template('unsubscribe_reason.html', token=token)
    else:
        return render_template('unsubscribe_error.html')

@app.route('/unsubscribe/submit', methods=['POST'])
def unsubscribe_submit():
    token = request.form['token']
    reason = request.form['reason']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Find the user based on the token
    cursor.execute("SELECT user_id FROM subscriptions WHERE token = ?", (token,))
    user_id = cursor.fetchone()

    if user_id:
        # Update the subscription status and reason
        cursor.execute("UPDATE subscriptions SET subscribed = 0, unsubscribe_reason = ? WHERE user_id = ?", (reason, user_id[0]))
        conn.commit()
        return redirect(url_for('unsubscribe_success'))
    else:
        return render_template('unsubscribe_error.html')

@app.route('/unsubscribe_success')
def unsubscribe_success():
    return "You have successfully unsubscribed from the newsletter."

@app.route('/unsubscribe_all')
def unsubscribe_all():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update the subscription status for all users
    cursor.execute("UPDATE subscriptions SET subscribed = 0")
    conn.commit()

    return redirect(url_for('unsubscribe_all_success'))

@app.route('/unsubscribe_all_success')
def unsubscribe_all_success():
    return "All users have been unsubscribed from the newsletter."

if __name__ == '__main__':
    init_db()
    app.run(debug=True)