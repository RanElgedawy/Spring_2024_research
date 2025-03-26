from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    """Create a new database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and insert sample data if needed."""
    conn = get_db()
    cursor = conn.cursor()
    # Create products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS carts")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            stock INTEGER
        )
    ''')
    # Create carts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    ''')
    # Insert sample products if table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            (1, 'Widget', 'A useful widget', 19.99, 10),
            (2, 'Gadget', 'A fancy gadget', 29.99, 0),   # out of stock
            (3, 'Doohickey', 'An interesting doohickey', 9.99, 5)
        ]
        cursor.executemany('''
            INSERT INTO products (id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_products)
    conn.commit()
    conn.close()

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve product information by product ID."""
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(dict(product))

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add a product (if in stock) to the user's cart.
    
    Expects:
    - Header "X-User-ID": user id (integer)
    - JSON body with key "product_id"
    """
    # Ensure user identification via header
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User ID missing in header'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    # Ensure JSON payload with product_id
    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({'error': 'Product ID is required in JSON body'}), 400
    product_id = data['product_id']
    
    conn = get_db()
    cursor = conn.cursor()
    # Check if the product exists and has stock available
    product = cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    if product['stock'] <= 0:
        conn.close()
        return jsonify({'error': 'Product is out of stock'}), 400
    
    # Add product to cart: if it already exists in the user's cart, increment quantity.
    existing_item = cursor.execute(
        "SELECT * FROM carts WHERE user_id = ? AND product_id = ?",
        (user_id, product_id)
    ).fetchone()
    if existing_item:
        cursor.execute(
            "UPDATE carts SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
    else:
        cursor.execute(
            "INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, 1)
        )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product added to cart successfully'})

@app.route('/cart', methods=['GET'])
def view_cart():
    """Retrieve the current cart items for the authenticated user.
    
    Expects header "X-User-ID" to specify the user.
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User ID missing in header'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    conn = get_db()
    items = conn.execute("SELECT * FROM carts WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(item) for item in items])

if __name__ == '__main__':
    init_db()
    # Run the server in debug mode. For production, consider using a proper WSGI server.
    app.run(debug=True)
