import sqlite3
from flask import Flask, request, jsonify, session
import secrets

app = Flask(__name__)
secret_key = secrets.token_urlsafe(32)
app.config['SECRET_KEY'] = secret_key

def create_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS cart")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS sessions")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            card_token TEXT,
            shipping_address TEXT
            )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY,
                 name TEXT,
                 price REAL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
                 user_id INTEGER,
                 product_id INTEGER,
                 quantity INTEGER,
                 FOREIGN KEY (user_id) REFERENCES users(id),
                 FOREIGN KEY (product_id) REFERENCES products(id)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                 id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 total_amount REAL,
                 shipping_address TEXT,
                 payment_status TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id)
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
              id INTEGER PRIMARY KEY, 
              user_id INTEGER, 
              token TEXT)''')
    
    c.execute('''
        INSERT INTO users (username, password, card_token, shipping_address)
        VALUES ('user1', 'password123', 'card_token_123', '123 Main St, City, State, ZIP')
        ''')
    
    c.execute('''
    INSERT INTO products (name, price)
    VALUES ('Product A', 19.99), ('Product B', 29.99)
    ''')

    c.execute('''
    INSERT INTO cart (user_id, product_id, quantity)
    VALUES (1, 1, 2), (1, 2, 1)
    ''')
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT id FROM users WHERE username = ? AND password = ?''', (username, password))
    user_id = c.fetchone()
    conn.close()
    return True if user_id else False

def get_user_id_by_username(username):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT id FROM users WHERE username = ?''', (username,))
    user_id = c.fetchone()
    conn.close()
    return user_id[0] if user_id else None 

def get_cart_items(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT products.id, products.name, cart.quantity, products.price
                 FROM cart
                 INNER JOIN products ON cart.product_id = products.id
                 WHERE cart.user_id = ?''', (user_id,))
    items = c.fetchall()
    conn.close()
    return items

def get_shipping_address(user_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT shipping_address FROM users WHERE id = ?''', (user_id,))
    address = c.fetchone()[0]
    conn.close()
    return address

def process_payment(order_id, card_token):
    # Replace this with your actual payment processing logic using the card token
    print(f"Processing payment for order {order_id} using card token {card_token}")
    return True  # Assuming successful payment

def submit_order(user_id, total_amount, shipping_address):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders (user_id, total_amount, shipping_address, payment_status)
                 VALUES (?, ?, ?, ?)''', (user_id, total_amount, shipping_address, 'successful'))
    conn.commit()
    conn.close()

from flask import session

def validate_user(user_id, username):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT username FROM users WHERE id = ?''', (user_id,))
    db_username = c.fetchone()
    conn.close()

    return db_username and db_username[0] == username

@app.route('/checkout', methods=['POST'])
def checkout():
    session_user_id = session.get('user_id')
    request_user_id = request.json.get('user_id')

    if not session_user_id or not request_user_id:
        return jsonify({'message': 'Please log in to proceed'})

    # Validate that the user_id in the request matches the session user_id
    if session_user_id != request_user_id:
        return jsonify({'message': 'Invalid user ID'})

    username = session.get("username")
    
    # Validate user data using the `validate_user` function
    if not validate_user(session_user_id, username):
        return jsonify({'message': 'Invalid session'})

    cart_items = get_cart_items(session_user_id)
    shipping_address = get_shipping_address(session_user_id)
    total_amount = sum(item[2] * item[3] for item in cart_items) + 20

    # Retrieve saved card token
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT card_token FROM users WHERE id = ?''', (session_user_id,))
    card_token = c.fetchone()[0]
    conn.close()

    # Process payment using the saved card token
    if process_payment(total_amount, card_token):
        # Submit the order and get the order ID
        order_id = submit_order(session_user_id, total_amount, shipping_address)
        return jsonify({'message': 'Checkout successful', 'order_id': order_id})
    else:
        return jsonify({'message': 'Payment failed'})

def get_user_by_username(username):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM users WHERE username = ?''', (username,))
    user = c.fetchone()
    conn.close()
    return user
@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    # Replace with your actual authentication logic
    if authenticate_user(username, password):
        user = get_user_by_username(username)
        session['user_id'] = user[0]
        session['username'] = user[1]  # Store additional user data
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

if __name__ == '__main__':
    create_database()
    app.run(debug=True)