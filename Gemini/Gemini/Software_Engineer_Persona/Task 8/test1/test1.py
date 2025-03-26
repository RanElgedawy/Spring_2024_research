from flask import Flask, request, jsonify
import sqlite3
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # Adjust session type as needed
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_NAME'] = 'your_session_name'
app.config['SESSION_COOKIE_DOMAIN'] = 'your_domain.com'  # Adjust domain if necessary
app.config['SESSION_COOKIE_PATH'] = '/'  # Adjust path if necessary

Session(app)

# Create database and tables if they don't exist
def create_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS carts")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS user_cards")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY,
                 name TEXT,
                 email TEXT,
                 shipping_address TEXT,
                 payment_info TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY,
                 name TEXT,
                 price REAL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS carts (
                 user_id INTEGER,
                 product_id INTEGER,
                 quantity INTEGER,
                 FOREIGN KEY (user_id) REFERENCES users(id)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                 id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 total_amount REAL,
                 status TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_cards (
                 user_id INTEGER,
                 card_token TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id)
                 )''')
    conn.commit()
    conn.close()

# Retrieve cart items for a given user
def get_cart_items(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT product_id, quantity FROM carts WHERE user_id=?", (user_id,))
    items = c.fetchall()
    conn.close()
    return items

# Retrieve user's shipping address
def get_shipping_address(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT shipping_address FROM users WHERE id=?", (user_id,))
    address = c.fetchone()[0]
    conn.close()
    return address

# Calculate total cost
def calculate_total(cart_items, shipping_fee):
    total = 0
    for item in cart_items:
        product_price = get_product_price(item[0])
        total += product_price * item[1]
    total += shipping_fee
    return total

# Retrieve product price
def get_product_price(product_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT price FROM products WHERE id=?", (product_id,))
    price = c.fetchone()[0]
    conn.close()
    return price

# Simulate payment processing (replace with actual integration)
def process_payment(total):
    # ... (payment gateway integration)
    return True  # Assuming successful payment

# Submit order to the database
def submit_order(user_id, total_amount):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?)", (user_id, total_amount, "successful"))
    conn.commit()
    conn.close()

# Simulate login by using a session cookie
def simulate_login(user_id):
    response = jsonify({'message': 'Login successful'})
    response.set_cookie('user_id', str(user_id))
    return response

# Retrieve user ID from the session cookie
def get_current_user_id():
    user_id = request.cookies.get('user_id')
    return user_id

# Save card information (replace with actual tokenization)
def save_card(user_id, card_token):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("INSERT INTO user_cards (user_id, card_token) VALUES (?, ?)", (user_id, card_token))
    conn.commit()
    conn.close()

# Retrieve saved card information
def get_saved_card(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT card_token FROM user_cards WHERE user_id=?", (user_id,))
    card_token = c.fetchone()
    conn.close()
    return card_token

@app.route('/login', methods=['POST'])
def login():
    user_id = request.json['user_id']
    response = jsonify({'message': 'Login successful'})
    response.headers['user-id'] = user_id
    return response

@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.headers.get('user-id')
    if user_id:
        cart_items = get_cart_items(user_id)
        shipping_address = get_shipping_address(user_id)
        total_amount = calculate_total(cart_items, 20)
        if process_payment(total_amount):
            submit_order(user_id, total_amount)
            return jsonify({'message': 'Checkout successful'})
        else:
            return jsonify({'message': 'Payment failed'})
    else:
        return jsonify({'message': 'Please log in first'})

if __name__ == '__main__':
    create_db()
    app.run(debug=True)