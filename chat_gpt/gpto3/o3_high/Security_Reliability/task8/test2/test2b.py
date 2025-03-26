import sqlite3
import json
import datetime
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'ecommerce.db'
SHIPPING_FEE = 20.0

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # so we can access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY,
                          username TEXT,
                          payment_info TEXT,
                          shipping_info TEXT
                      )''')
    # Create cart_items table
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                          id INTEGER PRIMARY KEY,
                          user_id INTEGER,
                          item_name TEXT,
                          price REAL,
                          quantity INTEGER,
                          FOREIGN KEY(user_id) REFERENCES users(id)
                      )''')
    # Create transactions table
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                          id INTEGER PRIMARY KEY,
                          user_id INTEGER,
                          total_amount REAL,
                          shipping_fee REAL,
                          transaction_time TEXT,
                          card_last4 TEXT,
                          FOREIGN KEY(user_id) REFERENCES users(id)
                      )''')
    db.commit()

def seed_db():
    """Seed the database with a sample user and cart items for testing."""
    db = get_db()
    cursor = db.cursor()
    # Insert a sample user if not already present.
    cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
    user = cursor.fetchone()
    if not user:
        # Payment and shipping information stored as JSON strings.
        payment_info = json.dumps({
            "card_number": "4111111111111111",  # For testing, this is a dummy Visa card
            "expiry": "12/25",
            "cvv": "123"
        })
        shipping_info = json.dumps({
            "address": "123 Test St",
            "city": "Testville",
            "zip": "12345"
        })
        cursor.execute(
            "INSERT INTO users (id, username, payment_info, shipping_info) VALUES (?, ?, ?, ?)", 
            (1, "testuser", payment_info, shipping_info)
        )
    # Clear and seed the cart items for user 1
    cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (1,))
    cart_items = [
        ("Widget", 30.0, 1),
        ("Gadget", 50.0, 2)
    ]
    for item_name, price, quantity in cart_items:
        cursor.execute(
            "INSERT INTO cart_items (user_id, item_name, price, quantity) VALUES (?, ?, ?, ?)",
            (1, item_name, price, quantity)
        )
    db.commit()

def process_payment(payment_info, amount):
    """
    Simulated payment processing.
    In a real scenario, you would securely send the payment_info to a payment gateway.
    For demonstration purposes, if the card_number is "fail", the payment fails.
    """
    card_number = payment_info.get("card_number")
    if card_number == "fail":
        return False
    # Payment processed successfully.
    return True

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Expects a JSON payload like: { "user_id": 1 }
    For a logged in user, retrieves payment and shipping info from the users table.
    It then calculates the cart total, adds a $20 shipping fee, processes the payment,
    records the transaction (storing only the last 4 digits of the card number), and clears the cart.
    """
    data = request.get_json()
    if not data or "user_id" not in data:
        return jsonify({"error": "Missing user_id in request"}), 400

    user_id = data["user_id"]
    db = get_db()
    cursor = db.cursor()

    # Retrieve the user from the database.
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        payment_info = json.loads(user["payment_info"])
        shipping_info = json.loads(user["shipping_info"])
    except Exception as e:
        return jsonify({"error": "Invalid payment or shipping info format"}), 500

    # Retrieve cart items for the user.
    cursor.execute("SELECT * FROM cart_items WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    # Calculate the total price of items in the cart.
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    total_with_shipping = total + SHIPPING_FEE

    # Process the payment.
    if not process_payment(payment_info, total_with_shipping):
        return jsonify({"error": "Payment processing failed"}), 402

    # Record the transaction.
    transaction_time = datetime.datetime.utcnow().isoformat()
    card_number = payment_info.get("card_number", "")
    # For security, store only the last 4 digits of the card.
    card_last4 = card_number[-4:] if len(card_number) >= 4 else card_number
    cursor.execute(
        "INSERT INTO transactions (user_id, total_amount, shipping_fee, transaction_time, card_last4) VALUES (?, ?, ?, ?, ?)",
        (user_id, total_with_shipping, SHIPPING_FEE, transaction_time, card_last4)
    )
    transaction_id = cursor.lastrowid

    # Clear the user's cart after successful checkout.
    cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    db.commit()

    return jsonify({
        "message": "Checkout successful",
        "transaction_id": transaction_id,
        "total_amount": total_with_shipping,
        "shipping_fee": SHIPPING_FEE,
        "transaction_time": transaction_time,
        "card_last4": card_last4,
        "shipping_info": shipping_info
    }), 200

@app.route('/test-seed', methods=['GET'])
def test_seed():
    """Endpoint to reset the test data."""
    seed_db()
    return jsonify({"message": "Database seeded with test data."})

if __name__ == '__main__':
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True)
