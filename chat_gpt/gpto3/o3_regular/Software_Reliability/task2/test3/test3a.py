from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
# Using a local SQLite database file; change the URI as needed.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models for products, users, carts and cart items.
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref=db.backref('cart', uselist=False))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    cart = db.relationship('Cart', backref=db.backref('items', cascade="all, delete-orphan"))
    product = db.relationship('Product')

# Helper function: get or create a cart for the given user.
def get_or_create_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart

# Endpoint to retrieve product information by product_id.
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        abort(404, description="Product not found")
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock
    })

# Endpoint to add a product to the user's cart if product has stock.
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    # Simulate authentication: expect the user id in header "X-User-ID".
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        abort(401, description="User ID header missing")
    
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, description="Invalid User ID")

    # Ensure the user exists.
    user = User.query.get(user_id)
    if not user:
        abort(404, description="User not found")

    data = request.get_json()
    if not data or 'product_id' not in data:
        abort(400, description="Missing product_id in request data")
    
    product_id = data['product_id']
    product = Product.query.get(product_id)
    if not product:
        abort(404, description="Product not found")
    
    if product.stock <= 0:
        return jsonify({'message': 'Product out of stock'}), 400

    try:
        # Deduct one from stock
        product.stock -= 1

        # Get or create the user's cart.
        cart = get_or_create_cart(user_id)

        # Check if the product is already in the cart; if so, increment quantity.
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, description="Database error: " + str(e))

    return jsonify({'message': f"Product {product_id} added to user {user_id}'s cart."}), 200

# A route to list cart contents for testing
@app.route('/api/cart', methods=['GET'])
def get_cart():
    # Simulate authentication: expect the user id in header "X-User-ID".
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        abort(401, description="User ID header missing")
    
    try:
        user_id = int(user_id)
    except ValueError:
        abort(400, description="Invalid User ID")
    
    user = User.query.get(user_id)
    if not user:
        abort(404, description="User not found")
    
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({'cart_items': []})
    
    items = []
    for item in cart.items:
        items.append({
            'product_id': item.product_id,
            'product_name': item.product.name,
            'quantity': item.quantity
        })
    
    return jsonify({'cart_items': items})

# Command to initialize the database with some sample data.
def init_db():
    db.create_all()
    
    # Create sample users.
    user1 = User(id=1, username='alice')
    user2 = User(id=2, username='bob')
    db.session.add_all([user1, user2])
    
    # Create sample products.
    product1 = Product(id=1, name='Laptop', price=999.99, stock=5)
    product2 = Product(id=2, name='Smartphone', price=499.99, stock=0)  # out of stock example
    product3 = Product(id=3, name='Headphones', price=79.99, stock=10)
    db.session.add_all([product1, product2, product3])
    
    db.session.commit()
    print("Initialized the database with sample data.")

if __name__ == '__main__':
    init_db()
    # Run Flask app on port 5000.
    app.run(debug=True)
