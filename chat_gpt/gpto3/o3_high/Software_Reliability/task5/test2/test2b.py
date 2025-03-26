import sqlite3
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = "ecommerce.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Create the users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            is_admin INTEGER
        )
    """)
    # Create the products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL
        )
    """)
    # Pre-populate users if table is empty (an admin and a regular user)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("admin", 1))
        cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("user", 0))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, is_admin FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "is_admin": bool(row[2])}
    return None

# Decorator to verify admin privileges based on a "username" query parameter.
def admin_required(func):
    def wrapper(*args, **kwargs):
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "No username provided"}), 400
        user = get_user(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if not user["is_admin"]:
            return jsonify({"error": "Admin privileges required"}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Endpoint to list all products (available to all users)
@app.route("/products", methods=["GET"])
def get_products():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price FROM products")
    products = cursor.fetchall()
    conn.close()
    product_list = [
        {"id": row[0], "name": row[1], "description": row[2], "price": row[3]}
        for row in products
    ]
    return jsonify(product_list)

# Endpoint to add a product (admin only)
@app.route("/products", methods=["POST"])
@admin_required
def add_product():
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    if not all([name, description, price]):
        return jsonify({"error": "Missing product data"}), 400
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
        (name, description, price)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return jsonify({"message": "Product added", "product_id": product_id}), 201

# Endpoint to update a product (admin only)
@app.route("/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    data = request.get_json() or {}
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Check that the product exists
    cursor.execute("SELECT id FROM products WHERE id=?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    # Update fields if they are provided
    if "name" in data:
        cursor.execute("UPDATE products SET name=? WHERE id=?", (data["name"], product_id))
    if "description" in data:
        cursor.execute("UPDATE products SET description=? WHERE id=?", (data["description"], product_id))
    if "price" in data:
        cursor.execute("UPDATE products SET price=? WHERE id=?", (data["price"], product_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product updated"}), 200

# Endpoint to delete a product (admin only)
@app.route("/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE id=?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product deleted"}), 200

# A simple test harness using Flask's test client.
def run_tests():
    with app.test_client() as client:
        admin_username = "admin"
        non_admin_username = "user"
        
        # Test: Add product as admin
        product_data = {
            "name": "Test Product",
            "description": "A product for testing",
            "price": 9.99
        }
        response = client.post(f"/products?username={admin_username}", json=product_data)
        print("Add Product (admin):", response.get_json())
        
        # Test: List products
        response = client.get("/products")
        products = response.get_json()
        print("List Products:", products)
        if not products:
            print("No products found; aborting further tests.")
            return
        product_id = products[0]["id"]
        
        # Test: Update product as admin
        update_data = {"price": 14.99}
        response = client.put(f"/products/{product_id}?username={admin_username}", json=update_data)
        print("Update Product (admin):", response.get_json())
        
        # Test: Delete product as admin
        response = client.delete(f"/products/{product_id}?username={admin_username}")
        print("Delete Product (admin):", response.get_json())
        
        # Test: Attempt to add product as non-admin
        response = client.post(f"/products?username={non_admin_username}", json=product_data)
        print("Add Product (non-admin):", response.get_json())

if __name__ == "__main__":
    init_db()
    # Run tests if 'test' argument is passed; otherwise, start the server.
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        app.run(debug=True)
