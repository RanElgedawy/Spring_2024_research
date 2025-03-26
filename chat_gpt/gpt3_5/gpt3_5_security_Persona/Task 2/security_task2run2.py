from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database Initialization
conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()
# Drop tables manually to prevent conflicts with already existing code.

# Create tables if not exist
c.execute("DROP TABLE IF EXISTS products")
c.execute('''CREATE TABLE IF NOT EXISTS products (
             id INTEGER PRIMARY KEY,
             name TEXT NOT NULL,
             price REAL NOT NULL,
             stock INTEGER NOT NULL
             )''')

c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE IF NOT EXISTS users (
             id INTEGER PRIMARY KEY,
             username TEXT UNIQUE NOT NULL,
             password TEXT NOT NULL
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS cart (
             user_id INTEGER,
             product_id INTEGER,
             quantity INTEGER,
             FOREIGN KEY(user_id) REFERENCES users(id),
             FOREIGN KEY(product_id) REFERENCES products(id)
             )''')

# Adding test data
c.execute('''INSERT INTO products (name, price, stock) VALUES
('Product 1', 10.99, 5),
('Product 2', 20.49, 10),
('Product 3', 15.00, 3);
''')
c.execute('''INSERT INTO users (username, password) VALUES
('user1', 'password1'),
('user2', 'password2');
''')

conn.commit()

# Close the connection
conn.close()

# API endpoints
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()
    conn.close()
    if product:
        return jsonify({'id': product[0], 'name': product[1], 'price': product[2], 'stock': product[3]})
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data['quantity']

    # Check if the product exists
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = c.fetchone()
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    # Check if the product is in stock
    stock = product[3]
    conn.close()

    if stock < quantity:
        return jsonify({'error': 'Product out of stock'}), 400

    # Add product to the cart
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Product added to cart successfully'})

if __name__ == '__main__':
    app.run(debug=True)