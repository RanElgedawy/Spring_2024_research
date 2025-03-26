from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
app.config['DATABASE'] = 'ecommerce.db'

# Function to get the database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

# Function to create tables in the database if they don't exist
def create_tables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                stock INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # Inserting test products
        cursor.execute("INSERT INTO products (name, price, stock) VALUES ('Test Product 1', 10.99, 100)")
        cursor.execute("INSERT INTO products (name, price, stock) VALUES ('Test Product 2', 20.49, 50)")
        cursor.execute("INSERT INTO products (name, price, stock) VALUES ('Test Product 3', 5.99, 200)")

        db.commit()

# Teardown function to close the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Endpoint to retrieve product information by ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if product:
        product_info = {
            'id': product[0],
            'name': product[1],
            'price': product[2],
            'stock': product[3]
        }
        return jsonify(product_info)
    else:
        return jsonify({'message': 'Product not found'}), 404

# Endpoint to add a product to the user's cart
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    if not user_id or not product_id or not quantity:
        return jsonify({'message': 'Incomplete data provided'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if product[3] < quantity:  # Checking if requested quantity exceeds stock
        return jsonify({'message': 'Insufficient stock'}), 400

    cursor.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    db.commit()

    return jsonify({'message': 'Product added to cart successfully'})

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)   