from flask import Flask, request, jsonify
import sqlite3
import os

DATABASE = 'ecommerce.db'

def init_db():
    # Remove existing database file for a clean slate (for testing/demo purposes)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS cart")

    # Create the users table
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL
    )
    ''')
    
    # Create the products table
    c.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL,
        stock INTEGER
    )
    ''')
    
    # Create the cart table linking users and products
    c.execute('''
    CREATE TABLE cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    ''')
    
    # Insert sample users
    c.execute("INSERT INTO users (username) VALUES (?)", ("alice",))
    c.execute("INSERT INTO users (username) VALUES (?)", ("bob",))
    
    # Insert sample products
    c.execute("INSERT INTO products (id, name, description, price, stock) VALUES (?,?,?,?,?)",
              (1, "Laptop", "A powerful laptop", 999.99, 5))
    c.execute("INSERT INTO products (id, name, description, price, stock) VALUES (?,?,?,?,?)",
              (2, "Mouse", "Wireless mouse", 29.99, 10))
    
    conn.commit()
    conn.close()

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    # This setting returns rows as dictionaries
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    # Convert the row to a dict
    return jsonify(dict(product))

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    # Allow the user to specify a quantity (default to 1 if not provided)
    quantity = data.get("quantity", 1)
    
    if not user_id or not product_id:
        return jsonify({"error": "Missing user_id or product_id"}), 400
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Verify the user exists
    user = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    # Retrieve the product and check its stock
    product = c.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    
    if product["stock"] < quantity:
        conn.close()
        return jsonify({"error": "Not enough stock available"}), 400
    
    # Reduce the product stock by the quantity added to the cart
    new_stock = product["stock"] - quantity
    c.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
    
    # Check if the product is already in the user's cart; if so, update the quantity.
    existing_cart = c.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id)).fetchone()
    if existing_cart:
        new_quantity = existing_cart["quantity"] + quantity
        c.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, existing_cart["id"]))
    else:
        c.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?)",
                  (user_id, product_id, quantity))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Product added to cart"}), 200

@app.route('/cart/<int:user_id>', methods=['GET'])
def view_cart(user_id):
    conn = get_db_connection()
    # Join the cart with products to provide product names and prices
    cart_items = conn.execute('''
        SELECT cart.id, cart.quantity, products.name, products.price
        FROM cart 
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    
    # Convert results into a list of dictionaries
    items = [dict(item) for item in cart_items]
    return jsonify({"cart": items})

if __name__ == '__main__':
    init_db()  # Initialize the database and create sample data
    app.run(debug=True)
