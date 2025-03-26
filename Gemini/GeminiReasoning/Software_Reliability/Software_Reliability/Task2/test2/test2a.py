from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def close_db(conn):
    if conn:
        conn.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        close_db(db)

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    close_db(conn)
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.execute(query, args)
    conn.commit()
    cur.close()
    close_db(conn)

# Assume user authentication middleware exists and provides the current user ID
def get_current_user_id():
    # In a real application, this would involve checking headers, sessions, etc.
    # For this example, we'll simulate it.
    # You might have a decorator like @login_required that sets the user ID.
    # For testing purposes, let's assume the user ID is passed in the request headers.
    user_id_header = request.headers.get('X-User-ID')
    if user_id_header and user_id_header.isdigit():
        return int(user_id_header)
    return None  # Or raise an error if user is not authenticated

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = query_db('SELECT product_id, name, description, price, stock FROM products WHERE product_id = ?', (product_id,), one=True)
    if product:
        return jsonify(dict(product))
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'message': 'User authentication required'}), 401

    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({'message': 'Missing product_id in request'}), 400

    product_id = data['product_id']
    quantity = data.get('quantity', 1)

    product = query_db('SELECT product_id, name, price, stock FROM products WHERE product_id = ?', (product_id,), one=True)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'message': f'Not enough stock for product {product_id}'}), 400

    # Check if the product is already in the user's cart
    existing_cart_item = query_db('SELECT cart_id, quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id), one=True)

    if existing_cart_item:
        new_quantity = existing_cart_item['quantity'] + quantity
        execute_db('UPDATE carts SET quantity = ? WHERE cart_id = ?', (new_quantity, existing_cart_item['cart_id']))
        message = f'Updated quantity for product {product_id} in cart'
    else:
        execute_db('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
        message = f'Added product {product_id} to cart'

    return jsonify({'message': message}), 201

if __name__ == '__main__':
    # This part is for testing purposes. In a real application, you would use a proper WSGI server.
    # You need to initialize the database first by running:
    # flask --app your_script_name.py initdb
    # Replace your_script_name.py with the name of this file.

    # Example of how to run the Flask development server
    print("To initialize the database, run: flask --app your_script_name.py initdb")
    print("Replace your_script_name.py with the name of this file.")
    print("Then, you can run this script to start the development server.")
    # app.run(debug=True) # Uncomment this line to run the development server