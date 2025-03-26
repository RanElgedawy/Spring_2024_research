from flask import Flask, request, jsonify, render_template_string
import sqlite3
from cryptography.fernet import Fernet

# Generate an encryption key (in a real app, securely store and manage this key)
KEY = Fernet.generate_key()
cipher = Fernet(KEY)

app = Flask(__name__)
DB_NAME = 'payment_cards.db'

def init_db():
    """Initialize the database and create the payment_cards table if it does not exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS payment_cards")
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_holder TEXT,
            expiry_date TEXT,
            card_number_encrypted BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

@app.route('/')
def index():
    # A simple HTML form to register a new payment card
    form_html = '''
    <h2>Register Payment Card</h2>
    <form method="post" action="/register_card">
        <label>User ID:</label><br>
        <input type="number" name="user_id" required><br><br>
        <label>Card Holder Name:</label><br>
        <input type="text" name="card_holder" required><br><br>
        <label>Card Number:</label><br>
        <input type="text" name="card_number" required><br><br>
        <label>Expiry Date (MM/YY):</label><br>
        <input type="text" name="expiry_date" required><br><br>
        <button type="submit">Register Card</button>
    </form>
    '''
    return render_template_string(form_html)

@app.route('/register_card', methods=['POST'])
def register_card():
    """Endpoint to register a new payment card."""
    try:
        user_id = request.form.get('user_id')
        card_holder = request.form.get('card_holder')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        
        # Basic validation: ensure required fields are provided
        if not all([user_id, card_number]):
            return "Missing required fields", 400
        
        # Encrypt the credit card number before storing it
        encrypted_card_number = cipher.encrypt(card_number.encode('utf-8'))
        
        # Insert the encrypted card data into the database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO payment_cards (user_id, card_holder, expiry_date, card_number_encrypted)
            VALUES (?, ?, ?, ?)
        """, (user_id, card_holder, expiry_date, encrypted_card_number))
        conn.commit()
        conn.close()
        
        return "Card registered successfully!"
    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/list_cards/<int:user_id>')
def list_cards(user_id):
    """
    For testing purposes, this endpoint retrieves all registered cards for a given user.
    It decrypts the card numbers to show that encryption works correctly.
    (In production, avoid decrypting and exposing sensitive card data.)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT id, user_id, card_holder, expiry_date, card_number_encrypted
        FROM payment_cards WHERE user_id = ?
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    
    cards = []
    for row in rows:
        # Decrypt the card number for demonstration (do not do this in production)
        decrypted_card_number = cipher.decrypt(row[4]).decode('utf-8')
        cards.append({
            "id": row[0],
            "user_id": row[1],
            "card_holder": row[2],
            "expiry_date": row[3],
            "card_number": decrypted_card_number
        })
    
    return jsonify(cards)

if __name__ == '__main__':
    # Run the Flask development server for testing
    app.run(debug=True)
