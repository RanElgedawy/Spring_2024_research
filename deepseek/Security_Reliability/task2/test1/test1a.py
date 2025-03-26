from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Database initialization
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        # Create tables if they don't exist
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        db.execute("DROP TABLE IF EXISTS users")
        db.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        db.commit()

init_db()

# Helper methods
def insert_sample_data():
    with app.app_context():
        db = get_db()
        # Insert sample product
        db.execute('''
            INSERT OR IGNORE INTO products (id, name, price, stock)
            VALUES (1, 'Wireless Mouse', 29.99, 10)
        ''')
        db.commit()

insert_sample_data()

# API Endpoints
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    product = db.execute(
        'SELECT id, name, price, stock FROM products WHERE id = ?',
        (product_id,)
    ).fetchone()
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(dict(product)), 200

@app.route('/cart/items', methods=['POST'])
def add_to_cart():
    # Authentication mock - In production, use proper authentication
    user_id = request.headers.get('X-User-ID')
    if not user_id or not user_id.isdigit():
        return jsonify({'error': 'Invalid user ID'}), 401
    
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
        if quantity <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid quantity or product ID'}), 400

    db = get_db()
    try:
        with db:  # Transaction starts
            # Check product availability
            product = db.execute(
                'SELECT stock FROM products WHERE id = ?',
                (product_id,)
            ).fetchone()
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
                
            if product['stock'] < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400

            # Check existing cart item
            cart_item = db.execute(
                '''SELECT quantity FROM cart 
                WHERE user_id = ? AND product_id = ?''',
                (user_id, product_id)
            ).fetchone()

            if cart_item:
                new_quantity = cart_item['quantity'] + quantity
                if new_quantity > product['stock']:
                    return jsonify({'error': 'Exceeds available stock'}), 400
                db.execute(
                    '''UPDATE cart SET quantity = ? 
                    WHERE user_id = ? AND product_id = ?''',
                    (new_quantity, user_id, product_id)
                )
            else:
                db.execute(
                    '''INSERT INTO cart (user_id, product_id, quantity)
                    VALUES (?, ?, ?)''',
                    (user_id, product_id, quantity)
                )
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

    return jsonify({'message': 'Item added to cart'}), 201

if __name__ == '__main__':
    app.run(debug=True)