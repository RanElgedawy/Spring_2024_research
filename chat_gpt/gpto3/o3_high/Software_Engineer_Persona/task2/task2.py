from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import sys

app = Flask(__name__)
# Use SQLite; the DB file will be created automatically if it doesn't exist.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Product model.
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

# Define the CartItem model.
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Endpoint to retrieve product information by product ID.
@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })
    else:
        return jsonify({'error': 'Product not found'}), 404

# Endpoint to add a product to the user's cart.
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    # Retrieve the user ID from the headers (simulate authentication).
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'User ID missing in headers'}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid User ID'}), 400

    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Request must contain product_id and quantity'}), 400

    try:
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except ValueError:
        return jsonify({'error': 'product_id and quantity must be integers'}), 400

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive integer'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Check if the product is already in the user's cart.
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    # Decrement the product stock to reflect the addition to the cart.
    product.stock -= quantity

    db.session.commit()

    return jsonify({
        'message': 'Product added to cart successfully',
        'cart_item': {
            'user_id': user_id,
            'product_id': product_id,
            'quantity': cart_item.quantity
        }
    })

# Initialize the database and seed it with sample products if none exist.
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        if Product.query.count() == 0:
            sample_products = [
                Product(name="Product A", price=9.99, stock=10),
                Product(name="Product B", price=19.99, stock=5),
                Product(name="Product C", price=29.99, stock=0)  # out of stock example
            ]
            db.session.bulk_save_objects(sample_products)
            db.session.commit()
            print("Sample products added to the database.")

# A simple test routine using Flask's test client.
def run_tests():
    init_db()
    with app.test_client() as client:
        print("\n--- Testing GET /api/product/1 ---")
        response = client.get('/api/product/1')
        print("Response:", response.get_json())

        print("\n--- Testing POST /api/cart with valid product and sufficient stock ---")
        headers = {'X-User-ID': '1'}
        response = client.post('/api/cart', json={'product_id': 1, 'quantity': 2}, headers=headers)
        print("Response:", response.get_json())

        print("\n--- Testing POST /api/cart with insufficient stock ---")
        response = client.post('/api/cart', json={'product_id': 2, 'quantity': 10}, headers=headers)
        print("Response:", response.get_json())

        print("\n--- Testing POST /api/cart with missing user header ---")
        response = client.post('/api/cart', json={'product_id': 1, 'quantity': 1})
        print("Response:", response.get_json())

# Entry point: run tests if "test" is provided as an argument; otherwise, start the server.
if __name__ == '__main__':
    if 'test' in sys.argv:
        run_tests()
    else:
        init_db()
        app.run(debug=True)
