import sqlite3
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

def create_database():
    """Creates necessary tables in the database."""
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS cart")
    c.execute("DROP TABLE IF EXISTS orders")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id TEXT PRIMARY KEY,
                 name TEXT,
                 email TEXT,
                 shipping_address TEXT,
                 payment_info TEXT
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS products (
                 product_id TEXT PRIMARY KEY,
                 name TEXT,
                 price REAL
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS cart (
                 user_id TEXT,
                 product_id TEXT,
                 quantity INTEGER,
                 FOREIGN KEY (user_id) REFERENCES users(user_id),
                 FOREIGN KEY (product_id) REFERENCES products(product_id)
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                 order_id TEXT PRIMARY KEY,
                 user_id TEXT,
                 total REAL,
                 status TEXT
                 )''')
    
    # Insert a user
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", ("user123", "John Doe", "johndoe@example.com", "123 Main St", "token123"))

    # Insert products
    c.execute("INSERT INTO products VALUES (?, ?, ?)", ("product1", "Product 1", 19.99))
    c.execute("INSERT INTO products VALUES (?, ?, ?)", ("product2", "Product 2", 29.99))

    # Add items to the user's cart
    c.execute("INSERT INTO cart VALUES (?, ?, ?)", ("user123", "product1", 2))
    c.execute("INSERT INTO cart VALUES (?, ?, ?)", ("user123", "product2", 1))

    conn.commit()
    conn.close()

def check_user_authentication(user_id):
    """Checks if the user is authenticated."""
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()

    conn.close()

    return user is not None

def checkout(user_id):
    """Processes a checkout request."""
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Retrieve cart items
    c.execute("SELECT product_id, quantity FROM cart WHERE user_id=?", (user_id,))
    cart_items = c.fetchall()

    # Calculate total
    total = 20.0  # Shipping fee
    for product_id, quantity in cart_items:
        c.execute("SELECT price FROM products WHERE product_id=?", (product_id,))
        price = c.fetchone()[0]
        total += price * quantity

    # Retrieve shipping address
    c.execute("SELECT shipping_address FROM users WHERE user_id=?", (user_id,))
    shipping_address = c.fetchone()

    if not shipping_address:
        conn.close()
        return jsonify({"error": "User not found"})
    shipping_address = shipping_address[0]

    # Check if user is authenticated
    if not check_user_authentication(user_id):
        return jsonify({"error": "User not authenticated"})

    # Retrieve saved card information (assuming stored in the 'users' table)
    c.execute("SELECT payment_info FROM users WHERE user_id=?", (user_id,))
    saved_card = c.fetchone()[0]

    # Use the saved card information for payment processing (replace with actual implementation)
    # ... (e.g., call a payment gateway API)

    # Simulate payment processing for demonstration
    payment_successful = True

    if payment_successful:
        # Submit order
        order_id = str(uuid.uuid4())
        c.execute("INSERT INTO orders VALUES (?, ?, ?, ?)", (order_id, user_id, total, "completed"))
        conn.commit()

        # Clear cart
        c.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        conn.commit()

    conn.close()

    return jsonify({"message": "Checkout successful" if payment_successful else "Payment failed"})

@app.route('/checkout', methods=['POST'])
def checkout_endpoint():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"})

    result = checkout(user_id)
    return result

if __name__ == "__main__":
    create_database()
    app.run(debug=True)