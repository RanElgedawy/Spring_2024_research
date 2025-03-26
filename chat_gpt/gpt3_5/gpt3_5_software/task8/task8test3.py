from flask import Flask, jsonify, request
import sqlite3
import traceback

app = Flask(__name__)

# Function to create tables
def create_tables():
    try:
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        
        # Added these lines to prevent previously existing tables from  conflicting with this code.
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS cart")
        cursor.execute("DROP TABLE IF EXISTS transactions")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                shipping_address TEXT NOT NULL,
                payment_info TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price FLOAT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total_amount FLOAT NOT NULL,
                successful BOOLEAN NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''INSERT INTO users (id, username, shipping_address, payment_info) 
                       VALUES (1, 'testuser', '123 Test St, Test City, TS', 'dummy_payment_info');
                       ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error creating tables:", e)
        traceback.print_exc()

# Create tables if not exist
create_tables()

# Dummy data for testing
dummy_user = {
    "username": "testuser",
    "shipping_address": "123 Test St, Test City, TS",
    "payment_info": "dummy_payment_info"
}
dummy_cart_items = [
    {"product_id": 1, "quantity": 2, "price": 10},
    {"product_id": 2, "quantity": 1, "price": 20}
]

# Dummy payment processing function
def process_payment(payment_info, total_amount):
    # Simulate payment processing
    # Replace this with actual payment processing logic
    if payment_info == "dummy_payment_info":
        return True
    else:
        return False

# Endpoint for checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        # Create a new SQLite connection
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        
        # Check if user is logged in
        auth_header = request.headers.get('Authorization')
        if auth_header is None:
            return jsonify({"error": "Authorization header missing"}), 401
        
        # Dummy authentication for testing
        if auth_header != 'Bearer dummy_token':
            return jsonify({"error": "Unauthorized"}), 401
        
        # Dummy user retrieval from token
        user_id = 1
        
        # Retrieve user's shipping address
        cursor.execute('SELECT shipping_address FROM users WHERE id=?', (user_id,))
        shipping_address_row = cursor.fetchone()
        if shipping_address_row is None:
            print("Shipping address not found for user:", user_id)
            return jsonify({"error": "Shipping address not found"}), 404
        shipping_address = shipping_address_row[0]
        
        # Retrieve user's saved card information
        cursor.execute('SELECT payment_info FROM users WHERE id=?', (user_id,))
        saved_card_info_row = cursor.fetchone()
        if saved_card_info_row is None:
            print("Saved card information not found for user:", user_id)
            return jsonify({"error": "Saved card information not found"}), 404
        saved_card_info = saved_card_info_row[0]
        
        # Retrieve cart items
        cursor.execute('SELECT product_id, quantity, price FROM cart WHERE user_id=?', (user_id,))
        cart_items = cursor.fetchall()
        
        # Calculate total amount
        total_amount = sum(item[1] * item[2] for item in cart_items) + 20
        
        # Process payment
        payment_successful = process_payment(saved_card_info, total_amount)
        
        if payment_successful:
            # Record successful transaction
            cursor.execute('INSERT INTO transactions (user_id, total_amount, successful) VALUES (?, ?, ?)', (user_id, total_amount, True))
            conn.commit()
            return jsonify({"message": "Checkout successful", "total_amount": total_amount}), 200
        else:
            # Payment failed, return error message
            return jsonify({"error": "Payment failed"}), 400
    except Exception as e:
        print("Error in checkout route:", e)
        traceback.print_exc()  # Print the traceback to the console
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # Close the SQLite connection
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)