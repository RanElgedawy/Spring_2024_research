from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'newsletter.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create table to store subscription data
    c.execute("DROP TABLE IF EXISTS subscriptions")
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed INTEGER DEFAULT 1,
            unsubscribe_reason TEXT
        )
    ''')
    # For testing purposes, insert a sample user
    try:
        c.execute("INSERT INTO subscriptions (email, subscribed) VALUES (?, ?)", ("test@example.com", 1))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """
    Endpoint to unsubscribe a user.
    Expects JSON data with at least:
      - email: User's email (identifier)
    Optionally, it accepts:
      - reason: A reason for unsubscribing.
    """
    # For simplicity, we get the email from the request. In a real app, verify using session info.
    data = request.get_json() or request.form
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    reason = data.get('reason', None)

    # Verify the user exists in our subscriptions table
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM subscriptions WHERE email = ?", (email,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Update the subscription status and record the reason if provided
    c.execute("""
        UPDATE subscriptions
        SET subscribed = 0,
            unsubscribe_reason = ?
        WHERE email = ?
    """, (reason, email))
    conn.commit()
    conn.close()

    return jsonify({'message': f'{email} has been unsubscribed', 'reason': reason})

# A simple HTML form to test the unsubscribe functionality
@app.route('/test_unsubscribe', methods=['GET'])
def test_unsubscribe():
    html_form = '''
    <!doctype html>
    <html>
      <head>
        <title>Test Unsubscribe</title>
      </head>
      <body>
        <h2>Test Newsletter Unsubscription</h2>
        <form action="/unsubscribe" method="post">
          <label>Email:</label><br>
          <input type="text" name="email" value="test@example.com" required><br><br>
          <label>Reason (optional):</label><br>
          <textarea name="reason" rows="4" cols="50"></textarea><br><br>
          <input type="submit" value="Unsubscribe">
        </form>
      </body>
    </html>
    '''
    return render_template_string(html_form)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
