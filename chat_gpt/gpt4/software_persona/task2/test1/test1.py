from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    cart = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

def initialize_database():
    with app.app_context():
        # Create the database and tables if they do not exist
        db.drop_all()
        db.create_all()

        # Check if there are any users or products in the database
        if not User.query.first():
            # Creating a test user
            db.session.add(User(username="testuser"))
            db.session.commit()

        if not Product.query.first():
            # Creating test products
            products = [
                Product(name="Product 1", price=10.99, stock=100),
                Product(name="Product 2", price=20.99, stock=50),
                Product(name="Product 3", price=30.99, stock=0)  # Out of stock
            ]
            db.session.bulk_save_objects(products)
            db.session.commit()

# API Endpoints
@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        }), 200
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock'}), 400

    # Add product to cart
    cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)

    # Update product stock
    product.stock -= quantity

    db.session.commit()

    return jsonify({'message': 'Product added to cart'}), 200

# To test the API, create a test user and product
@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({'message': 'API is working'}), 200

if __name__ == '__main__':
    initialize_database()  # Ensure the database is initialized before the app runs
    app.run(debug=True)