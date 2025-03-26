from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS carts")

        # Create products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
        ''')

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        ''')

        # Create carts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        ''')

        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Route to get product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = query_db('SELECT * FROM products WHERE id = ?', [product_id], one=True)
    if product:
        product_info = {
            'id': product[0],
            'name': product[1],
            'price': product[2],
            'stock': product[3]
        }
        return jsonify(product_info), 200
    else:
        return jsonify({"error": "Product not found"}), 404

# Route to add product to cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    # Validate input
    if not user_id or not product_id or not quantity:
        return jsonify({"error": "Missing user_id, product_id, or quantity"}), 400

    # Check if product exists and if enough stock is available
    product = query_db('SELECT * FROM products WHERE id = ?', [product_id], one=True)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product[3] < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    # Check if user exists
    user = query_db('SELECT * FROM users WHERE id = ?', [user_id], one=True)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Add product to user's cart
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO carts (user_id, product_id, quantity)
        VALUES (?, ?, ?)
    ''', (user_id, product_id, quantity))

    # Update product stock
    cursor.execute('''
        UPDATE products
        SET stock = stock - ?
        WHERE id = ?
    ''', (quantity, product_id))

    db.commit()

    return jsonify({"message": "Product added to cart successfully"}), 200

# Route to initialize the database with sample data
@app.route('/init', methods=['GET'])
def initialize_data():
    db = get_db()
    cursor = db.cursor()

    # Insert sample products
    cursor.execute('INSERT INTO products (name, price, stock) VALUES (?, ?, ?)', ('Product A', 100.0, 10))
    cursor.execute('INSERT INTO products (name, price, stock) VALUES (?, ?, ?)', ('Product B', 150.0, 5))

    # Insert sample users
    cursor.execute('INSERT INTO users (name) VALUES (?)', ('User 1',))
    cursor.execute('INSERT INTO users (name) VALUES (?)', ('User 2',))

    db.commit()

    return jsonify({"message": "Database initialized with sample data"}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)