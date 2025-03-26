from flask import Flask, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_secret_key"
DATABASE = "ecommerce.db"

def get_db():
    # Connect to the SQLite database.
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Automatically create the users and payment_cards tables.
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                expiration_date TEXT NOT NULL,
                cvv TEXT NOT NULL,
                cardholder_name TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.commit()

@app.before_first_request
def setup():
    init_db()
    # Create a dummy user "testuser" if not already present.
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
        user = cursor.fetchone()
        if not user:
            cursor.execute("INSERT INTO users (username) VALUES (?)", ("testuser",))
            conn.commit()

@app.route('/')
def index():
    # Simulate a logged-in user by setting the session to the dummy user.
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ("testuser",))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['id']
    # Display a form to add a new payment card.
    return """
    <h2>Add a Payment Card</h2>
    <form method="post" action="/add_card">
      Card Number: <input type="text" name="card_number" required><br>
      Expiration Date (MM/YY): <input type="text" name="expiration_date" required><br>
      CVV: <input type="text" name="cvv" required><br>
      Cardholder Name: <input type="text" name="cardholder_name"><br>
      <input type="submit" value="Add Card">
    </form>
    <br>
    <a href="/test">Test: List My Cards</a>
    """

@app.route('/add_card', methods=["POST"])
def add_card():
    # Ensure that the user is logged in.
    if "user_id" not in session:
        return "User not logged in", 401

    user_id = session["user_id"]
    card_number = request.form.get("card_number")
    expiration_date = request.form.get("expiration_date")
    cvv = request.form.get("cvv")
    cardholder_name = request.form.get("cardholder_name")

    # Basic validation.
    if not (card_number and expiration_date and cvv):
        return "Missing required card information", 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO payment_cards (user_id, card_number, expiration_date, cvv, cardholder_name)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, card_number, expiration_date, cvv, cardholder_name))
        conn.commit()

    # After adding, redirect back to the form.
    return redirect(url_for("index"))

@app.route('/test')
def test_cards():
    # List all payment cards for the logged-in user.
    if "user_id" not in session:
        return "User not logged in", 401

    user_id = session["user_id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payment_cards WHERE user_id = ?", (user_id,))
        cards = cursor.fetchall()
        html = "<h2>My Payment Cards</h2><ul>"
        for card in cards:
            html += "<li>Card Number: {} | Exp: {} | CVV: {} | Cardholder: {}</li>".format(
                card["card_number"],
                card["expiration_date"],
                card["cvv"],
                card["cardholder_name"] if card["cardholder_name"] else "N/A"
            )
        html += "</ul><a href='/'>Back</a>"
    return html

if __name__ == "__main__":
    # Run the Flask app.
    app.run(debug=True)
