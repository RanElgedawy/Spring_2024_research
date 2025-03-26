from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app
app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)  # Number of products in stock

# Define the Cart model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Initialize the database
db.drop_all()
db.create_all()

# Route to retrieve product information by product ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })
    return jsonify({'error': 'Product not found'}), 404

# Route to add product to cart (only if it's in stock)
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    # Fetch the product
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Check if the product is in stock
    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Add to cart (or update existing cart item)
    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)

    # Update the product stock
    product.stock -= quantity

    # Save changes to the database
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'})

# Route to retrieve the cart for a specific user
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'message': 'Cart is empty'})

    cart_data = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        cart_data.append({
            'product_id': item.product_id,
            'product_name': product.name,
            'quantity': item.quantity,
            'price': product.price,
            'total_price': product.price * item.quantity
        })

    return jsonify(cart_data)

# Function to seed initial data for testing purposes
def seed_data():
    # Add some test products
    products = [
        Product(name='Product 1', price=19.99, stock=10),
        Product(name='Product 2', price=29.99, stock=5),
        Product(name='Product 3', price=9.99, stock=0)  # Out of stock product
    ]
    db.session.bulk_save_objects(products)
    db.session.commit()

if __name__ == '__main__':
    # Seed the database with test data
    seed_data()

    # Run the Flask app
    app.run(debug=True)