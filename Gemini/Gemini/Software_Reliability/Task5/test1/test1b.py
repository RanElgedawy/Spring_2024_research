from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the database (create if it doesn't exist)
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )''')
    conn.commit()
    conn.close()

# Verify admin privileges
def is_admin(user_id):
    # Replace this with your actual user authentication logic
    # For now, let's assume a simple check
    admin_users = [1, 2]  # Replace with actual admin user IDs
    return user_id in admin_users

@app.route('/products', methods=['GET', 'POST', 'PUT', 'DELETE'])
def products():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = 1  # Replace with actual logged-in user ID

    if not is_admin(user_id):
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        cursor.execute('SELECT * FROM products')
        rows = cursor.fetchall()
        return jsonify(rows)

    elif request.method == 'POST':
        name = request.json['name']
        description = request.json['description']
        price = request.json['price']
        cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
        conn.commit()
        return jsonify({'message': 'Product added successfully'})

    elif request.method == 'PUT':
        product_id = request.json['id']
        name = request.json['name']
        description = request.json['description']
        price = request.json['price']
        cursor.execute('UPDATE products SET name=?, description=?, price=? WHERE id=?', (name, description, price, product_id))
        conn.commit()
        return jsonify({'message': 'Product updated successfully'})

    elif request.method == 'DELETE':
        product_id = request.json['id']
        cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
        return jsonify({'message': 'Product deleted successfully'})

    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)