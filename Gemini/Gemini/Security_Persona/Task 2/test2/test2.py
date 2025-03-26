from flask import Flask, request, jsonify
import sqlite3
import threading

# Connect to database
conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS products")
c.execute("DROP TABLE IF EXISTS carts")
c.execute("DROP TABLE IF EXISTS users")
# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    price REAL,
    quantity INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT
)''')

# Insert sample users
c.execute("INSERT INTO users (username, password) VALUES ('user1', 'password123')")
c.execute("INSERT INTO users (username, password) VALUES ('user2', 'password456')")

# Insert sample products
c.execute("INSERT INTO products (name, description, price, quantity) VALUES ('Product 1', 'Description of Product 1', 19.99, 10)")
c.execute("INSERT INTO products (name, description, price, quantity) VALUES ('Product 2', 'Description of Product 2', 29.99, 5)")

conn.commit()

app = Flask(__name__)

class ThreadLocalConnection(threading.local):
    def __init__(self):
        self.conn = None

thread_local_conn = ThreadLocalConnection()

@app.before_request
def before_request():
    thread_local_conn.conn = sqlite3.connect('ecommerce.db')
    thread_local_conn.conn.cursor()

@app.teardown_request
def teardown_request(exception):
    if thread_local_conn.conn:
        thread_local_conn.conn.close()

@app.route('/products/<int:product_id>')
def get_product(product_id):
    c = thread_local_conn.conn.cursor()
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()
    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/<int:user_id>/products/<int:product_id>', methods=['POST'])
def add_to_cart(user_id, product_id):
    c = thread_local_conn.conn.cursor()
    c.execute('SELECT quantity FROM products WHERE id = ?', (product_id,))
    product_quantity = c.fetchone()

    if product_quantity is None:
        return jsonify({'error' : 'Product not found'}), 404

    if product_quantity[0] > 0:
        c.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, 1)', (user_id, product_id))
        thread_local_conn.conn.commit()
        return jsonify({'message': 'Product added to cart'})
    else:
        return jsonify({'error': 'Product is out of stock'}), 400

@app.route('/carts/<int:user_id>')
def get_cart(user_id):
    c = thread_local_conn.conn.cursor()
    c.execute('SELECT products.name, products.price, carts.quantity FROM carts JOIN products ON carts.product_id = products.id WHERE carts.user_id = ?', (user_id,))
    cart = c.fetchall()
    return jsonify(cart)

if __name__ == '__main__':
    app.run(debug=True)