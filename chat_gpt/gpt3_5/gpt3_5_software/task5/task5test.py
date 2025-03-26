from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, admin BOOLEAN)''')

    # Create products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, description TEXT)''')

     # Insert an admin user (for testing purposes)
    c.execute("INSERT INTO users (username, password, admin) VALUES (?, ?, ?)",
              ('admin', 'admin_password', True))
    
    conn.commit()
    conn.close()

# Function to check if the logged-in user is an admin
def is_admin(username):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("SELECT admin FROM users WHERE username = ?", (username,))
    result = c.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        return False

# Route to add a new product
@app.route('/product/add', methods=['POST'])
def add_product():
    if not is_admin(request.form['username']):
        return jsonify({'error': 'User does not have admin privileges'})

    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
              (request.form['name'], request.form['price'], request.form['description']))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Product added successfully'})

# Route to remove a product
@app.route('/product/remove', methods=['POST'])
def remove_product():
    if not is_admin(request.form['username']):
        return jsonify({'error': 'User does not have admin privileges'})

    product_id = request.form['product_id']

    # Check if the product exists
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    existing_product = c.fetchone()
    conn.close()

    if existing_product is None:
        return jsonify({'error': 'Product with ID {} does not exist'.format(product_id)})

    # Product exists, proceed with removal
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("DELETE FROM products WHERE id = ?", (product_id,))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Product removed successfully'})

# Route to modify a product
@app.route('/product/modify', methods=['POST'])
def modify_product():
    if not is_admin(request.form['username']):
        return jsonify({'error': 'User does not have admin privileges'})

    product_id = request.form['product_id']

    # Check if the product exists
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    existing_product = c.fetchone()
    conn.close()

    if existing_product is None:
        return jsonify({'error': 'Product with ID {} does not exist'.format(product_id)})

    # Product exists, proceed with modification
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?",
              (request.form['name'], request.form['price'], request.form['description'], product_id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Product modified successfully'})


if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
