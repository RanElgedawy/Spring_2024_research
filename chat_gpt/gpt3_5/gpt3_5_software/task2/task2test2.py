from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database initialization and helper functions
def initialize_database():
    conn = sqlite3.connect('store.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Carts
                 (user_id INTEGER, product_id INTEGER, quantity INTEGER)''')
    # Added line for testing
    c.execute('''INSERT INTO Products (name, price, stock) VALUES
    ('Product A', 10.99, 20),
    ('Product B', 15.49, 15),
    ('Product C', 5.99, 30);
    ''')

    conn.commit()
    conn.close()

def get_product_info(product_id):
    conn = sqlite3.connect('store.db')
    c = conn.cursor()
    c.execute("SELECT * FROM Products WHERE id=?", (product_id,))
    product = c.fetchone()
    conn.close()
    return product

def add_to_cart(user_id, product_id, quantity):
    conn = sqlite3.connect('store.db')
    c = conn.cursor()
    c.execute("INSERT INTO Carts VALUES (?, ?, ?)", (user_id, product_id, quantity))
    c.execute("UPDATE Products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()

# API endpoints
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = get_product_info(product_id)
    if product:
        return jsonify({'id': product[0], 'name': product[1], 'price': product[2], 'stock': product[3]})
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart_api():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    product = get_product_info(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product[3] < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    add_to_cart(user_id, product_id, quantity)
    return jsonify({'message': 'Product added to cart successfully'})

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
