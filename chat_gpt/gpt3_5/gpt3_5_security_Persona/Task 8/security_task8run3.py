from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    # To prevent previously defined tables from interfering with this program
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        total_amount REAL,
                        successful BOOLEAN
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS carts (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        item_id INTEGER,
                        quantity INTEGER
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        address TEXT,
                        city TEXT,
                        country TEXT,
                        card_number TEXT,
                        expiration_date TEXT,
                        cvv TEXT
                    )''')
    # Insert some sample data for testing
    cursor.execute("INSERT INTO carts (user_id, item_id, quantity) VALUES (?, ?, ?)", (1, 1, 2))
    cursor.execute("INSERT INTO carts (user_id, item_id, quantity) VALUES (?, ?, ?)", (1, 2, 1))
    cursor.execute("INSERT INTO users (id, name, email, address, city, country, card_number, expiration_date, cvv) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (1, 'John Doe', 'john@example.com', '123 Main St', 'Example City', 'Example Country', '1234 5678 9012 3456', '12/25', '123'))
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Route for checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    # Check if the user is logged in
    if 'user_id' in request.json:
        user_id = request.json['user_id']
        # Get user's cart and address information from the database
        cart = get_user_cart(user_id)
        user_address = get_user_address(user_id)
        user_card_info = get_user_card_info(user_id)

        if cart and user_address:
            # Calculate total amount including shipping fee
            total_amount = calculate_total_amount(cart)

            # Add shipping fee
            total_amount += 20

            # Process payment using saved card information if available
            if user_card_info:
                payment_successful = process_payment(user_card_info, total_amount)
            else:
                # Placeholder payment info
                payment_info = {
                    'card_number': '1234 5678 9012 3456',
                    'expiration_date': '12/25',
                    'cvv': '123'
                }
                payment_successful = process_payment(payment_info, total_amount)

            if payment_successful:
                # Record successful transaction in the database
                record_transaction(user_id, total_amount)
                return jsonify({'message': 'Payment successful! Transaction recorded.'}), 200
            else:
                return jsonify({'message': 'Payment failed! Please try again later.'}), 400
        else:
            return jsonify({'message': 'No items in the cart or address information missing!'}), 400
    else:
        return jsonify({'message': 'User not logged in!'}), 400

# Function to get user's cart from the database
def get_user_cart(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,))
    cart = cursor.fetchall()
    conn.close()
    return cart

# Function to get user's address information from the database
def get_user_address(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("SELECT address, city, country FROM users WHERE id = ?", (user_id,))
    address = cursor.fetchone()
    conn.close()
    return address

# Function to get user's saved card information from the database
def get_user_card_info(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("SELECT card_number, expiration_date, cvv FROM users WHERE id = ?", (user_id,))
    card_info = cursor.fetchone()
    conn.close()
    return card_info

# Placeholder function to calculate total amount
def calculate_total_amount(cart):
    # Placeholder logic to calculate total amount
    total_amount = 0
    for item in cart:
        # Retrieve item price from database based on item_id
        item_price = 10  # Placeholder price
        total_amount += item[3] * item_price  # quantity * price
    return total_amount

# Placeholder function to process payment
def process_payment(payment_info, total_amount):
    # Placeholder logic to process payment
    # For demonstration purposes, always return True
    return True

# Function to record transaction in the database
def record_transaction(user_id, total_amount):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id, total_amount, successful) VALUES (?, ?, ?)",
                   (user_id, total_amount, True))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)