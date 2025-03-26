import sqlite3
from flask import Flask, request, jsonify, g

DATABASE = 'ecommerce.db'

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        # Return results as dicts
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Create tables if they don't exist.
    db.executescript('''
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS carts;
                     
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    ''')
    db.commit()
    # Insert sample data if tables are empty
    cur = db.execute('SELECT COUNT(*) as count FROM users')
    if cur.fetchone()['count'] == 0:
        db.executemany('INSERT INTO users (username, email) VALUES (?,?)',
                       [('alice', 'alice@example.com'), ('bob', 'bob@example.com')])
    cur = db.execute('SELECT COUNT(*) as count FROM products')
    if cur.fetchone()['count'] == 0:
        db.executemany('INSERT INTO products (name, description, price, stock) VALUES (?,?,?,?)',
                       [('Laptop', 'A powerful laptop', 999.99, 10),
                        ('Headphones', 'Noise-cancelling headphones', 199.99, 5),
                        ('Mouse', 'Wireless mouse', 29.99, 0)])  # out of stock
    db.commit()

@app.before_first_request
def setup():
    init_db()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    # Use a parameterized query to prevent SQL injection
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    # Convert row to dict
    product_data = dict(product)
    return jsonify(product_data)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON data'}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'error': 'user_id and product_id are required'}), 400

    db = get_db()
    # Check that the user exists
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        return jsonify({'error': 'User not found'}), 404

    # Check that the product exists and has enough stock
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Add to cart using a parameterized query.
    # For simplicity, if the same product is added again, we increment the quantity.
    cart_item = db.execute('SELECT * FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id)).fetchone()
    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        # Ensure new quantity does not exceed available stock.
        if product['stock'] < new_quantity:
            return jsonify({'error': 'Not enough stock available for the updated quantity'}), 400
        db.execute('UPDATE carts SET quantity = ? WHERE id = ?', (new_quantity, cart_item['id']))
    else:
        db.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?,?,?)', (user_id, product_id, quantity))
    db.commit()
    return jsonify({'message': 'Product added to cart successfully'}), 200

# A simple test function to verify the endpoints using Flask's test client.
def run_tests():
    with app.test_client() as client:
        # Test GET /product/<id>
        response = client.get('/product/1')
        print("GET /product/1:", response.json)

        response = client.get('/product/999')
        print("GET /product/999 (not exist):", response.json)

        # Test POST /cart/add
        # Add a product that is in stock
        response = client.post('/cart/add', json={'user_id': 1, 'product_id': 1, 'quantity': 2})
        print("POST /cart/add (valid):", response.json)
        
        # Try to add a product that is out of stock
        response = client.post('/cart/add', json={'user_id': 1, 'product_id': 3, 'quantity': 1})
        print("POST /cart/add (out of stock):", response.json)

        # Test SQL injection prevention by sending malicious input (it will be treated as a normal value)
        response = client.get('/product/1; DROP TABLE products;')
        print("GET /product/1; DROP TABLE products;:", response.status_code, response.data.decode())

if __name__ == '__main__':
    import sys
    if 'test' in sys.argv:
        # Run tests if "test" argument is provided
        with app.app_context():
            init_db()
        run_tests()
    else:
        app.run(debug=True)
