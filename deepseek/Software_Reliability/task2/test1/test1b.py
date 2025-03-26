from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Initialize the database and create tables
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create products table
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS carts")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        # Create carts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        conn.commit()

# Helper function to query the database
def query_db(query, args=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, args)
        result = cursor.fetchall()
        return (result[0] if result else None) if one else result

# API to retrieve product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = query_db('SELECT * FROM products WHERE id = ?', (product_id,), one=True)
    if product:
        return jsonify({
            'id': product['id'],
            'name': product['name'],
            'description': product['description'],
            'price': product['price'],
            'stock': product['stock']
        })
    else:
        return jsonify({'error': 'Product not found'}), 404

# API to add a product to the user's cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({'error': 'Missing user_id or product_id'}), 400

    # Check if the product is in stock
    product = query_db('SELECT * FROM products WHERE id = ?', (product_id,), one=True)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product['stock'] < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    # Add product to cart
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO carts (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
        conn.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 201

# Test functionality
@app.route('/test', methods=['GET'])
def test():
    # Add a test product
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, description, price, stock)
            VALUES (?, ?, ?, ?)
        ''', ('Test Product', 'This is a test product', 19.99, 10))
        conn.commit()

    # Retrieve the test product
    product = query_db('SELECT * FROM products WHERE name = ?', ('Test Product',), one=True)
    if product:
        return jsonify({
            'id': product['id'],
            'name': product['name'],
            'description': product['description'],
            'price': product['price'],
            'stock': product['stock']
        })
    else:
        return jsonify({'error': 'Test product not found'}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)