import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Database setup: create tables for users, products, cart, and orders.
def setup_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")
    
    # Create Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        address TEXT,
                        payment_info TEXT
                      )''')
    
    # Create Products table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        price REAL
                      )''')
    
    # Create Cart table
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(product_id) REFERENCES products(id)
                      )''')

    # Create Orders table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        total_price REAL,
                        shipping_fee REAL,
                        status TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                      )''')
    
    conn.commit()
    conn.close()

# Helper function to get the user's cart items
def get_cart_items(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    query = '''SELECT p.id, p.name, p.price, c.quantity 
               FROM products p
               JOIN cart c ON p.id = c.product_id
               WHERE c.user_id = ?'''
    
    cursor.execute(query, (user_id,))
    items = cursor.fetchall()
    conn.close()

    return items

# Helper function to get user profile including address and payment info
def get_user_profile(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name, address, payment_info FROM users WHERE id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()

    return profile

# Mock payment processing function
def process_payment(payment_info, amount):
    # Here we just simulate a successful payment, you can add actual payment gateway logic
    return True

# Checkout route
@app.route('/checkout/<int:user_id>', methods=['POST'])
def checkout(user_id):
    # Get cart items
    cart_items = get_cart_items(user_id)

    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    # Get user profile (address and payment information)
    user_profile = get_user_profile(user_id)

    if not user_profile:
        return jsonify({"error": "User profile not found"}), 404

    user_name, shipping_address, payment_info = user_profile

    # Calculate the total price of the cart
    total_price = sum(item[2] * item[3] for item in cart_items)  # price * quantity for each item

    # Apply shipping fee ($20)
    shipping_fee = 20
    total_price_with_shipping = total_price + shipping_fee

    # Process payment (mock)
    if not process_payment(payment_info, total_price_with_shipping):
        return jsonify({"error": "Payment failed"}), 400

    # Record the successful order in the database
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO orders (user_id, total_price, shipping_fee, status) 
                      VALUES (?, ?, ?, ?)''', (user_id, total_price_with_shipping, shipping_fee, 'Success'))

    conn.commit()
    conn.close()

    return jsonify({"message": "Order successfully placed", "total": total_price_with_shipping})

# Route to test the database setup and functionality
@app.route('/test_setup', methods=['GET'])
def test_setup():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Insert dummy data for testing
    cursor.execute("INSERT INTO users (name, address, payment_info) VALUES ('John Doe', '123 Main St', 'card_123')")
    cursor.execute("INSERT INTO products (name, price) VALUES ('Laptop', 1000.00), ('Headphones', 200.00)")
    cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (1, 1, 1), (1, 2, 2)")

    conn.commit()
    conn.close()

    return jsonify({"message": "Test data inserted"})

# Initialize the database
setup_database()

if __name__ == '__main__':
    app.run(debug=True)
