import sqlite3
from flask import Flask, request, jsonify, g

app = Flask(__name__)
app.config['DATABASE'] = 'ecommerce.db'

def get_db_connection():
    conn = getattr(g, '_database', None)
    if conn is None:
        conn = g._database = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
    return conn

@app.teardown_appcontext
def close_connection(exception):
    conn = getattr(g, '_database', None)
    if conn is not None:
        conn.close()

def init_db():
    with app.app_context():
        conn = get_db_connection()
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS products")
        conn.execute("DROP TABLE IF EXISTS cart")
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE(user_id, product_id)
            )
        ''')
        # Insert test data
        conn.execute('INSERT OR IGNORE INTO users (id, username) VALUES (1, "testuser")')
        conn.execute('''
            INSERT OR IGNORE INTO products (id, name, price, stock)
            VALUES (1, 'Test Product', 19.99, 10)
        ''')
        conn.commit()

init_db()

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    return jsonify(dict(product)) if product else ('', 404)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Missing X-User-ID header'}), 400
    
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing product_id or quantity'}), 400
    
    product_id = data['product_id']
    quantity = data['quantity']
    
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity'}), 400

    conn = get_db_connection()
    try:
        # Verify user exists
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify product exists and get stock
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Calculate total requested quantity
        cart_item = conn.execute('''
            SELECT quantity FROM cart 
            WHERE user_id = ? AND product_id = ?
        ''', (user_id, product_id)).fetchone()
        
        current_quantity = cart_item['quantity'] if cart_item else 0
        new_quantity = current_quantity + quantity

        # Check stock availability
        if new_quantity > product['stock']:
            return jsonify({'error': 'Insufficient stock'}), 400

        # Update database
        if cart_item:
            conn.execute('''
                UPDATE cart SET quantity = ?
                WHERE user_id = ? AND product_id = ?
            ''', (new_quantity, user_id, product_id))
        else:
            conn.execute('''
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, product_id, new_quantity))
        
        conn.commit()
        return jsonify({'message': 'Product added to cart successfully'}), 200

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': 'Database error'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)