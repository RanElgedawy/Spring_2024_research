import sqlite3
from flask import Flask, request, jsonify, g
from datetime import datetime

app = Flask(__name__)
DATABASE = 'transactions.db'

def get_db():
    """Establish a connection to the SQLite database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection after the app context ends."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create transactions table if it does not exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS transactions")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                items TEXT,
                total REAL,
                transaction_date TEXT
            )
        ''')
        db.commit()

init_db()

def process_payment(card_info, amount):
    """
    Simulate processing a payment securely.
    In production, you would send the card information over a secure channel
    to a payment gateway. Here, we simulate success if the card number ends with an even digit.
    """
    try:
        # Using only a simple check for demonstration; do not use this in production.
        if int(card_info.get("card_number")[-1]) % 2 == 0:
            return True
        else:
            return False
    except Exception:
        return False

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Checkout endpoint.
    Expects a JSON payload with:
      - user_id: The logged-in user's ID.
      - cart_items: A list of items with their prices (and optionally, an id).
      - payment_info: The payment card details.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    cart_items = data.get('cart_items')
    payment_info = data.get('payment_info')
    shipping_fee = 20.0

    if not user_id or not cart_items or not payment_info:
        return jsonify({"error": "Missing required information"}), 400

    # Calculate the total: subtotal of items + shipping fee
    subtotal = sum(item.get('price', 0) for item in cart_items)
    total = subtotal + shipping_fee

    # Process payment securely (simulate)
    if not process_payment(payment_info, total):
        return jsonify({"error": "Payment failed"}), 402

    # Record successful transaction
    # For simplicity, we record a comma-separated list of item IDs.
    items_str = ", ".join([str(item.get('id', 'unknown')) for item in cart_items])
    transaction_date = datetime.now().isoformat()

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, items, total, transaction_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, items_str, total, transaction_date))
    db.commit()

    return jsonify({
        "message": "Checkout successful",
        "total": total,
        "transaction_date": transaction_date
    }), 200

@app.route('/test', methods=['GET'])
def test_checkout():
    """
    A testing endpoint to simulate a checkout.
    This endpoint constructs a sample payload and posts it to the /checkout endpoint.
    """
    test_payload = {
        "user_id": 1,
        "cart_items": [
            {"id": 101, "name": "Widget", "price": 50},
            {"id": 102, "name": "Gadget", "price": 30}
        ],
        "payment_info": {
            "card_number": "4242424242424242",  # Ends with 2, simulating a successful payment
            "expiration": "12/25",
            "cvv": "123"
        }
    }
    # Using the Flask test client to simulate an internal POST request
    with app.test_client() as client:
        response = client.post('/checkout', json=test_payload)
        return response.get_data(as_text=True), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
