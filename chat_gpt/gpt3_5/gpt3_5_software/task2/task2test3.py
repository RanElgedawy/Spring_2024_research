from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to initialize the database and add example products
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    # Manually added to prevent problems with tables conflicting with already existing ones from other files.
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS carts")
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (product_id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)''')
    
    # Insert example products
    products = [
        (1, "Laptop", 999.99, 10),
        (2, "Mouse", 19.99, 50),
        (3, "Keyboard", 49.99, 30)
    ]
    c.executemany('INSERT INTO products (product_id, name, price, stock) VALUES (?, ?, ?, ?)', products)
    
    # Create carts table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS carts
                 (user_id INTEGER, product_id INTEGER, quantity INTEGER, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(product_id) REFERENCES products(product_id))''')
    
    conn.commit()
    conn.close()

# Function to retrieve product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
    product = c.fetchone()
    conn.close()
    if product:
        return jsonify({'product_id': product[0], 'name': product[1], 'price': product[2], 'stock': product[3]}), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

# Function to add products with stock to cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data['quantity']

    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Check if product exists and has sufficient stock
    c.execute('SELECT stock FROM products WHERE product_id = ?', (product_id,))
    stock = c.fetchone()
    if not stock:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    if stock[0] < quantity:
        conn.close()
        return jsonify({'error': 'Insufficient stock'}), 400

    # Add product to the cart
    c.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))

    # Update stock
    new_stock = stock[0] - quantity
    c.execute('UPDATE products SET stock = ? WHERE product_id = ?', (new_stock, product_id))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Product added to cart successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)