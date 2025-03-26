from flask import Flask, request, jsonify, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = "ecommerce.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Connect to the SQLite database (it will be created if it doesn't exist)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    """Create the tables and insert some sample data if they do not exist."""
    db = get_db()
    cur = db.cursor()
    
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')
    
    # Create products table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    
    # Insert sample users if table is empty
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        users = [
            ('admin_user', 1),
            ('regular_user', 0)
        ]
        cur.executemany("INSERT INTO users (username, is_admin) VALUES (?, ?)", users)
    
    # Insert sample products if table is empty
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ('Widget A', 'A useful widget', 19.99, 100),
            ('Gadget B', 'A fancy gadget', 29.99, 50)
        ]
        cur.executemany("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", products)
    
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def check_admin(user_id):
    """Check if the provided user_id corresponds to an admin user."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if user and user["is_admin"] == 1:
        return True
    return False

def get_user_from_request():
    """Simulate the current logged-in user based on a query parameter (user_id)."""
    user_id = request.args.get("user_id")
    if not user_id:
        return None, jsonify({"error": "user_id query parameter is required"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return None, jsonify({"error": "user_id must be an integer"}), 400
    return user_id, None, None

@app.route('/products', methods=['GET'])
def list_products():
    """List all products."""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products")
    products = [dict(row) for row in cur.fetchall()]
    return jsonify(products)

@app.route('/products/add', methods=['POST'])
def add_product():
    """Add a new product (admin only)."""
    user_id, error_response, status = get_user_from_request()
    if error_response:
        return error_response, status

    if not check_admin(user_id):
        return jsonify({"error": "Unauthorized: admin privileges required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    name = data.get("name")
    description = data.get("description", "")
    price = data.get("price")
    stock = data.get("stock")

    if not name or price is None or stock is None:
        return jsonify({"error": "Missing required fields: name, price, stock"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
        (name, description, price, stock)
    )
    db.commit()
    product_id = cur.lastrowid
    return jsonify({"message": "Product added", "product_id": product_id}), 201

@app.route('/products/modify/<int:product_id>', methods=['PUT'])
def modify_product(product_id):
    """Modify an existing product (admin only)."""
    user_id, error_response, status = get_user_from_request()
    if error_response:
        return error_response, status

    if not check_admin(user_id):
        return jsonify({"error": "Unauthorized: admin privileges required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    fields = []
    values = []
    for field in ['name', 'description', 'price', 'stock']:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    if not fields:
        return jsonify({"error": "No valid fields provided to update"}), 400

    values.append(product_id)
    db = get_db()
    cur = db.cursor()
    cur.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?", values)
    db.commit()

    if cur.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product updated"})

@app.route('/products/delete/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (admin only)."""
    user_id, error_response, status = get_user_from_request()
    if error_response:
        return error_response, status

    if not check_admin(user_id):
        return jsonify({"error": "Unauthorized: admin privileges required"}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()

    if cur.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product deleted"})

if __name__ == '__main__':
    # Remove the existing database for a clean start (optional)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    with app.app_context():
        init_db()
    print("Database initialized with sample users and products.")
    print("Sample admin user: user_id=1, regular user: user_id=2")
    app.run(debug=True)
