from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    carts = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    carts = db.relationship('Cart', backref='product', lazy=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)

# Create tables and sample data
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create test user if not exists
    if not User.query.get(1):
        test_user = User(id=1, username="testuser")
        db.session.add(test_user)
    
    # Create test product if not exists
    if not Product.query.get(1):
        test_product = Product(id=1, name="Test Product", price=19.99, stock=10)
        db.session.add(test_product)
    
    db.session.commit()

# Helper function to get current user
def get_current_user():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    return User.query.get(int(user_id))

# API Endpoints
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock
    })

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id or quantity < 1:
        return jsonify({"error": "Invalid request"}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product.stock < quantity:
        return jsonify({"error": "Insufficient stock"}), 400
    
    # Check if product already in cart
    cart_item = Cart.query.filter_by(user_id=user.id, product_id=product_id).first()
    
    try:
        if cart_item:
            # Update existing cart item
            if (cart_item.quantity + quantity) > product.stock:
                return jsonify({"error": "Cannot add more than available stock"}), 400
            cart_item.quantity += quantity
        else:
            # Create new cart item
            cart_item = Cart(user_id=user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        
        # Commit changes
        db.session.commit()
        return jsonify({
            "message": "Product added to cart",
            "cart_item": {
                "product_id": product_id,
                "quantity": cart_item.quantity
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Testing
@app.cli.command()
def test():
    """Run the tests"""
    import pytest
    import sys
    sys.exit(pytest.main(["-v", "-s", "app.py"]))

if __name__ == '__main__':
    app.run(debug=True)