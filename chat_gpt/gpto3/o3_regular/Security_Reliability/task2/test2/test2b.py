import sqlite3
from flask import Flask, request, jsonify, g

DATABASE = 'ecommerce.db'
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Enable foreign keys and use row factory for easier dict access
        db = g._database = sqlite3.connect(DATABASE)
        db.execute("PRAGMA foreign_keys = ON")
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("DROP TABLE IF EXISTS product")
    db.execute("DROP TABLE IF EXISTS cart")

    # Create product table if it doesn't exist
    db.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    # Create cart table; assuming one cart item per row per user.
    db.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES product(id)
        )
    ''')
    # Seed sample products (if table empty)
    cur = db.execute('SELECT COUNT(*) FROM product')
    if cur.fetchone()[0] == 0:
        sample_products = [
            (1, 'Widget A', 19.99, 10),
            (2, 'Widget B', 29.99, 0),   # Out of stock
            (3, 'Widget C', 9.99, 5)
        ]
        db.executemany('INSERT INTO product (id, name, price, stock) VALUES (?, ?, ?, ?)', sample_products)
    db.commit()

@app.before_first_request
def setup():
    init_db()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cur = db.execute('SELECT * FROM product WHERE id = ?', (product_id,))
    product = cur.fetchone()
    if product:
        return jsonify(dict(product))
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    db = get_db()
    data = request.get_json()
    # Expecting user_id, product_id and quantity in the JSON payload
    if not data or 'user_id' not in data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing required fields: user_id, product_id, quantity'}), 400
    
    try:
        user_id = int(data['user_id'])
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except ValueError:
        return jsonify({'error': 'Invalid data types provided'}), 400

    if quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    # Check if product exists and has sufficient stock
    cur = db.execute('SELECT stock FROM product WHERE id = ?', (product_id,))
    result = cur.fetchone()
    if not result:
        return jsonify({'error': 'Product not found'}), 404

    available_stock = result['stock']
    if available_stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Update the product stock (subtract the quantity being added)
    new_stock = available_stock - quantity
    db.execute('UPDATE product SET stock = ? WHERE id = ?', (new_stock, product_id))
    
    # Insert or update the cart. For simplicity, this example always inserts a new row.
    db.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
               (user_id, product_id, quantity))
    db.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 200

# --- Test routine ---
# Run a simple test when executing this script directly.
if __name__ == '__main__':
    # Start the Flask app in testing mode
    app.testing = True
    with app.test_client() as client:
        print("Retrieving product with id 1:")
        resp = client.get('/product/1')
        print(resp.get_json())

        print("Attempting to add product id 1 to user 100's cart (quantity 3):")
        resp = client.post('/cart/add', json={'user_id': 100, 'product_id': 1, 'quantity': 3})
        print(resp.get_json())

        print("Trying to add out-of-stock product id 2:")
        resp = client.post('/cart/add', json={'user_id': 100, 'product_id': 2, 'quantity': 1})
        print(resp.get_json())

        # Show product info after adding to cart to verify stock reduction.
        print("Retrieving product with id 1 after cart addition:")
        resp = client.get('/product/1')
        print(resp.get_json())
    
    # Optionally, uncomment the line below to run the server normally.
    # app.run(debug=True)
