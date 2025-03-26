import sqlite3
from flask import Flask, request, jsonify

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

        self.cursor.execute("DROP TABLE IF EXISTS products")
        self.cursor.execute("DROP TABLE IF EXISTS carts")
        self.cursor.execute("DROP TABLE IF EXISTS cart_items")

        # Create tables if they don't exist
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                                id INTEGER PRIMARY KEY,
                                name TEXT,
                                price REAL,
                                stock INTEGER
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS carts (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                                cart_id INTEGER,
                                product_id INTEGER,
                                quantity INTEGER,
                                FOREIGN KEY (cart_id) REFERENCES carts(id),
                                FOREIGN KEY (product_id) REFERENCES products(id)
                            )''')
        self.conn.commit()

    # ... other database operations (e.g., insert, update, delete)

app = Flask(__name__)
db = Database('ecommerce.db')  # Replace with your desired database file

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    # Fetch product information from the database, ensuring security against SQL injection
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/api/carts', methods=['POST'])
def add_to_cart():
    # Add a product to the user's cart, checking for stock availability
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    # Check if the product is in stock
    cursor = db.cursor()
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    stock = cursor.fetchone()[0]
    if stock < quantity:
        return jsonify({'error': 'Product is out of stock'}), 400

    # Add the product to the cart
    # ... (code to add product to cart)

    return jsonify({'message': 'Product added to cart'})

# ... other API endpoints as needed