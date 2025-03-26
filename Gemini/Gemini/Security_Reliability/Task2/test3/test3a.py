from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Create a function to handle product retrieval
def get_product(product_id):
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    result = cursor.fetchone()
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Product not found"}), 404

# Create a function to handle adding products to the cart
def add_to_cart(user_id, product_id, quantity):
    # Check if the product is in stock
    cursor.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
    product_quantity = cursor.fetchone()[0]
    if product_quantity >= quantity:
        # Add the product to the cart
        cursor.execute("INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
        conn.commit()
        return jsonify({"message": "Product added to cart"})
    else:
        return jsonify({"error": "Product out of stock"}), 400

# API routes
@app.route('/products/<int:product_id>')
def get_product_by_id(product_id):
    return get_product(product_id)

@app.route('/cart', methods=['POST'])
def add_to_cart_api():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')
    return add_to_cart(user_id, product_id, quantity)

if __name__ == '__main__':
    app.run(debug=True)