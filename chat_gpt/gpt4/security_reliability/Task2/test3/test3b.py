from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)

# Database Configuration
DB_CONFIG = {
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost',
    'database': 'ecommerce_db'
}

# Connect to MySQL
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied: Incorrect username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    return None

# Create Cart Table (For simplicity)
def create_cart_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            cart_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# 1. Retrieve Product Information
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT product_id, name, description, price, stock FROM products WHERE product_id = %s"
    cursor.execute(query, (product_id,))
    product = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if product:
        return jsonify(product), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

# 2. Add Product to Cart
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not all([user_id, product_id, quantity]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if product exists and is in stock
    cursor.execute("SELECT stock FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    if product['stock'] < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Insert product into cart
    query = "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, product_id, quantity))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'message': 'Product added to cart'}), 200

# 3. Save Cart Information
@app.route('/api/cart/save', methods=['POST'])
def save_cart():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'Missing required field: user_id'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve cart items for the user
    cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        return jsonify({'error': 'No items in the cart'}), 400

    # Here you could implement logic to process the order, such as reducing stock, creating an order record, etc.
    
    cursor.close()
    conn.close()

    return jsonify({'message': 'Cart saved successfully', 'cart_items': cart_items}), 200

if __name__ == '__main__':
    create_cart_table()  # Create the cart table if it doesn't exist
    app.run(debug=True)