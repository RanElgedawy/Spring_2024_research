import sqlite3
import hashlib
import secrets
import base64
import datetime
import flask

app = flask.Flask(__name__)

def create_database():
    global conn, c
    conn = sqlite3.connect('newsletter.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  password TEXT,
                  subscribed BOOLEAN DEFAULT 1,
                  token TEXT)''')
    
    # Insert some test data
    for email, password in [('user1@example.com', 'password123'), ('user2@example.com', 'password456'), ('user3@example.com', 'password789')]:
        token = secrets.token_urlsafe(32)
        c.execute("INSERT INTO users (email, password, token) VALUES (?, ?, ?)", (email, password, token))

    conn.commit()
    conn.close()


def generate_unsubscribe_link(user_id):
    # Retrieve the user's token from the database
    c.execute("SELECT token FROM users WHERE id=?", (user_id,))
    user_token = c.fetchone()[0]  # Assuming the token is the first element in the fetched row

    if not user_token:
        # Handle case where user doesn't have a token (e.g., error message)
        return None

    expiration_time = datetime.datetime.now() + datetime.timedelta(days=7)
    encoded_data = base64.urlsafe_b64encode(f"{user_id}:{user_token}:{expiration_time.strftime('%Y-%m-%d %H:%M:%S')}".encode()).decode()
    unsubscribe_link = f"http://localhost:5000/unsubscribe/{encoded_data}"  # Updated link to localhost:5000
    return unsubscribe_link

def unsubscribe_confirmation(encoded_data):
    global conn, c
    try:
        # Decode the user ID, token, and expiration time
        user_id, token, expiration_time = base64.urlsafe_b64decode(encoded_data.encode()).decode().split(":")
        # Verify the token and expiration time
        c.execute("SELECT id FROM users WHERE id=? AND token=? AND subscribed=1 AND expiration_time >= ?", (user_id, token, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        if c.fetchone():
            return flask.render_template('unsubscribe_confirmation.html', encoded_data=encoded_data)
        else:
            return flask.render_template('unsubscribe_error.html')
    except Exception as e:
        # Handle decoding errors or invalid tokens
        print(f"Error processing unsubscribe link: {e}")
        return flask.render_template('unsubscribe_error.html')

@app.route('/unsubscribe/<encoded_data>')
def unsubscribe_page(encoded_data):
    return unsubscribe_confirmation(encoded_data)

@app.route('/unsubscribe/submit', methods=['POST'])
def unsubscribe_submit():
    global conn, c
    encoded_data = flask.request.form['encoded_data']
    reason = flask.request.form['reason']

    try:
        # Decode the user ID, token, and expiration time
        user_id, token, expiration_time = base64.urlsafe_b64decode(encoded_data.encode()).decode().split(":")
        # Verify the token and expiration time
        c.execute("SELECT id FROM users WHERE id=? AND token=? AND subscribed=1 AND expiration_time >= ?", (user_id, token, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        if c.fetchone():
            c.execute("UPDATE users SET subscribed=0, reason=?, token='' WHERE id=?", (reason, user_id))
            conn.commit()
            # Send a confirmation email (replace with your email sending logic)
            send_confirmation_email(user_id, reason)
            return flask.redirect('/')
        else:
            return flask.render_template('unsubscribe_error.html')
    except Exception as e:
        # Handle decoding errors or invalid tokens
        print(f"Error processing unsubscribe link: {e}")
        return flask.render_template('unsubscribe_error.html')

def send_confirmation_email(user_id, reason):
    # For testing purposes, print the unique link to the terminal
    print(f"Confirmation email would be sent to user {user_id} with reason: {reason}")
    # Replace this with your actual email sending logic

@app.route('/unsubscribe/all')
def unsubscribe_all():
    global conn, c
    try:
        c.execute("UPDATE users SET subscribed=0")
        conn.commit()
        return flask.render_template('unsubscribe_all_success.html')
    except Exception as e:
        print(f"Error unsubscribing all users: {e}")
        return flask.render_template('unsubscribe_error.html')
    
if __name__ == '__main__':
    generate_unsubscribe_link("user1@example.com")
    create_database()
    app.run()