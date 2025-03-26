from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Database connection setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Initialize database with some test data
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS carts")
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        ''')

        # Sample data
        cursor.execute('INSERT OR IGNORE INTO users (username) VALUES ("john_doe")')
        cursor.execute('INSERT OR IGNORE INTO products (name, price, stock) VALUES ("Laptop", 999.99, 10)')
        cursor.execute('INSERT OR IGNORE INTO products (name, price, stock) VALUES ("Phone", 499.99, 5)')

        db.commit()

# Close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Retrieve product info by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT id, name, price, stock FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if product:
        return jsonify({
            'id': product[0],
            'name': product[1],
            'price': product[2],
            'stock': product[3]
        })
    else:
        return jsonify({'error': 'Product not found'}), 404

# Add product to cart (only if it has stock)
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    username = data.get('username')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    db = get_db()
    cursor = db.cursor()

    # Retrieve user info
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_id = user[0]

    # Retrieve product info
    cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    stock = product[0]

    if stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Add to cart
    cursor.execute('''
    INSERT INTO carts (user_id, product_id, quantity)
    VALUES (?, ?, ?)
    ''', (user_id, product_id, quantity))

    # Update product stock
    new_stock = stock - quantity
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))

    db.commit()

    return jsonify({'message': 'Product added to cart successfully'})


if __name__ == '__main__':
    # Initialize the database and start the Flask application
    init_db()
    app.run(debug=True)