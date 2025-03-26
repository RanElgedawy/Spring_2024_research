from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Database setup
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    schema_sql = """
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS carts;
    DROP TABLE IF EXISTS cart_items;

    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
    );

    CREATE TABLE carts (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE cart_items (
        id INTEGER PRIMARY KEY,
        cart_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(cart_id) REFERENCES carts(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """

    conn = get_db()
    conn.executescript(schema_sql)
    conn.commit()

def insert_sample_data():
    conn = get_db()
    cur = conn.cursor()

    # Insert sample products
    cur.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                ('Product 1', 'Description for product 1', 19.99, 100))
    cur.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                ('Product 2', 'Description for product 2', 29.99, 50))
    cur.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                ('Product 3', 'Description for product 3', 9.99, 200))
    cur.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                ('Product 4', 'Description for product 4', 49.99, 0))  # Out of stock product

    # Commit the changes
    conn.commit()
    cur.close()

# Helper functions
def execute_query(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    return cur

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# API Endpoints
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = query_db('SELECT * FROM products WHERE id = ?', (product_id,), one=True)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(dict(product))

@app.route('/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = query_db('SELECT * FROM products WHERE id = ? AND stock >= ?', (product_id, quantity), one=True)
    if product is None:
        return jsonify({'error': 'Product not in stock or does not exist'}), 400

    cart = query_db('SELECT * FROM carts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,), one=True)
    if cart is None:
        execute_query('INSERT INTO carts (user_id) VALUES (?)', (user_id,))
        cart = query_db('SELECT * FROM carts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,), one=True)

    execute_query('INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)',
                  (cart['id'], product_id, quantity))
    
    execute_query('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))
    
    return jsonify({'message': 'Product added to cart successfully'})

@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    cart = query_db('SELECT * FROM carts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,), one=True)
    if cart is None:
        return jsonify({'error': 'Cart not found'}), 404
    
    items = query_db('SELECT p.name, p.price, ci.quantity FROM cart_items ci JOIN products p ON ci.product_id = p.id WHERE ci.cart_id = ?', (cart['id'],))
    
    return jsonify({'cart': [dict(item) for item in items]})

# Application startup logic
with app.app_context():
    init_db()            # Initialize the database schema
    insert_sample_data() # Insert sample data into the database

if __name__ == '__main__':
    app.run(debug=True)