from flask import Flask, request, jsonify, g
import sqlite3

DATABASE = 'ecommerce.db'
app = Flask(__name__)

# Utility function to get DB connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Function to create tables and seed initial data
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS cart_items")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
        ''')
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        # Create cart table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')

        # Seed sample data if not already present
        # Seed users
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            users = [
                (1, 'alice'),
                (2, 'bob')
            ]
            cursor.executemany('INSERT INTO users (id, username) VALUES (?, ?)', users)
        
        # Seed products
        cursor.execute('SELECT COUNT(*) FROM products')
        if cursor.fetchone()[0] == 0:
            products = [
                (1, 'T-Shirt', 'A comfortable cotton t-shirt', 19.99, 10),
                (2, 'Jeans', 'Stylish blue jeans', 49.99, 5),
                (3, 'Sneakers', 'Running shoes', 89.99, 0)  # Out of stock
            ]
            cursor.executemany('INSERT INTO products (id, name, description, price, stock) VALUES (?, ?, ?, ?, ?)', products)

        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# API endpoint to retrieve product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    # Convert row to dict
    product_dict = {key: product[key] for key in product.keys()}
    return jsonify(product_dict), 200

# API endpoint to add product to cart (only if product has stock)
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    # User authentication: assume user id is provided in header
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'error': 'Missing user identification in header'}), 401
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user id'}), 400

    # Parse JSON body
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Request JSON must include product_id and quantity'}), 400
    try:
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
        if quantity <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Invalid product_id or quantity'}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if product exists and has enough stock
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'error': 'Insufficient stock available'}), 400

    # Optional: check if user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Add product to cart: if the product is already in the cart for the user, update quantity
    cursor.execute('SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    cart_item = cursor.fetchone()
    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        cursor.execute('UPDATE cart_items SET quantity = ? WHERE id = ?', (new_quantity, cart_item['id']))
    else:
        cursor.execute('INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    
    # Update product stock
    new_stock = product['stock'] - quantity
    cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product_id))
    db.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 200

# A simple test route to display cart items for a user (for testing purposes)
@app.route('/cart', methods=['GET'])
def view_cart():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'error': 'Missing user identification in header'}), 401
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user id'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT ci.id, p.name, ci.quantity, p.price
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = ?
    ''', (user_id,))
    items = cursor.fetchall()
    cart_items = []
    for item in items:
        cart_items.append({
            'cart_item_id': item['id'],
            'product_name': item['name'],
            'quantity': item['quantity'],
            'price': item['price']
        })
    return jsonify({'cart_items': cart_items}), 200

if __name__ == '__main__':
    init_db()
    print("Initialized database with sample data.")
    print("Run the server and use the following test instructions:")
    print("1. Retrieve a product: curl http://127.0.0.1:5000/product/1")
    print("2. Add a product to a cart (user id in header):")
    print("   curl -X POST -H 'Content-Type: application/json' -H 'X-User-Id: 1' -d '{\"product_id\": 1, \"quantity\": 2}' http://127.0.0.1:5000/cart/add")
    print("3. View cart items: curl -H 'X-User-Id: 1' http://127.0.0.1:5000/cart")
    app.run(debug=True)
