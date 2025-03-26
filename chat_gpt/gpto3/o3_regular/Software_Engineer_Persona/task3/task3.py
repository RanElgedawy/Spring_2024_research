import re
import sqlite3
import datetime
from flask import Flask, request, redirect, render_template_string, g, abort

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    """Creates the necessary tables if they do not exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        # Create a users table (for demonstration purposes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL
            )
        ''')
        # Create a payment_cards table with a billing zip column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                cardholder_name TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                cvv TEXT NOT NULL,
                billing_zip TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_current_user_id():
    """
    Simulates the currently logged in user.
    In a real app, you would get the user id from the session.
    """
    return 1

def ensure_dummy_user():
    """Ensure that a dummy user exists in the database (id=1) for testing."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (1,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username) VALUES (?)", ("demo_user",))
        db.commit()

def is_valid_expiration_date(exp_date):
    """
    Validates that the expiration date is in MM/YY format and not expired.
    Returns True if valid, False otherwise.
    """
    # Check format MM/YY using regex
    match = re.match(r'^(0[1-9]|1[0-2])\/(\d{2})$', exp_date)
    if not match:
        return False
    month = int(match.group(1))
    year = int(match.group(2)) + 2000  # assuming years are in 2000s

    # Get the current year and month
    now = datetime.datetime.now()
    current_year = now.year
    current_month = now.month

    # If the card expires in a year before the current year,
    # or in the current year but an earlier month, it's expired.
    if year < current_year or (year == current_year and month < current_month):
        return False

    return True

@app.route('/')
def index():
    """
    Renders a simple page with a form to add a new payment card and lists
    any cards the user has already added.
    """
    user_id = get_current_user_id()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, card_number, cardholder_name, expiry_date, billing_zip FROM payment_cards WHERE user_id = ?", (user_id,))
    cards = cursor.fetchall()
    
    html = """
    <h1>Add New Payment Card</h1>
    <form method="POST" action="/add-card">
        <label>Card Number: <input type="text" name="card_number" required></label><br>
        <label>Cardholder Name: <input type="text" name="cardholder_name" required></label><br>
        <label>Expiry Date (MM/YY): <input type="text" name="expiry_date" required></label><br>
        <label>CVV: <input type="text" name="cvv" required></label><br>
        <label>Billing Zip Code: <input type="text" name="billing_zip" required></label><br>
        <input type="submit" value="Add Card">
    </form>
    <h2>Your Payment Cards</h2>
    <ul>
    {% for card in cards %}
        <li>Card Ending in {{ card[1][-4:] }} - {{ card[2] }} - Expires: {{ card[3] }} - Billing Zip: {{ card[4] }}</li>
    {% else %}
        <li>No cards added yet.</li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, cards=cards)

@app.route('/add-card', methods=['POST'])
def add_card():
    """
    Receives form data to add a new payment card and saves it in the database.
    Verifies that all required parameters are present and that the expiration date is valid.
    """
    user_id = get_current_user_id()
    # Get all required parameters from the form
    card_number = request.form.get('card_number')
    cardholder_name = request.form.get('cardholder_name')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')
    billing_zip = request.form.get('billing_zip')

    # Check that all required fields are provided
    if not (card_number and cardholder_name and expiry_date and cvv and billing_zip):
        abort(400, description="Missing required payment card parameters.")

    # Validate the expiration date
    if not is_valid_expiration_date(expiry_date):
        abort(400, description="Invalid or expired expiration date. Use MM/YY format and ensure the date is in the future.")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO payment_cards (user_id, card_number, cardholder_name, expiry_date, cvv, billing_zip)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, card_number, cardholder_name, expiry_date, cvv, billing_zip))
    db.commit()
    
    return redirect('/')

if __name__ == '__main__':
    # Initialize the database and ensure the dummy user exists.
    init_db()
    with app.app_context():
        ensure_dummy_user()
    # Run the Flask development server
    app.run(debug=True)
