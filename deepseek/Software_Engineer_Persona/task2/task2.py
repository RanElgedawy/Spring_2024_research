from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship('Product', backref='carts')

# Create tables (only if they don't exist)
with app.app_context():
    db.drop_all()
    db.create_all()

# Helper function to get user from header
def get_authenticated_user():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    return User.query.get(int(user_id))

# API Endpoints
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock
    })

@app.route('/cart', methods=['POST'])
def add_to_cart():
    user = get_authenticated_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing product_id or quantity'}), 400
    
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.stock < data['quantity']:
        return jsonify({'error': 'Insufficient stock'}), 400

    # Check if product already in cart
    cart_item = Cart.query.filter_by(
        user_id=user.id,
        product_id=product.id
    ).first()

    if cart_item:
        new_quantity = cart_item.quantity + data['quantity']
        if product.stock < new_quantity:
            return jsonify({'error': 'Total quantity exceeds available stock'}), 400
        cart_item.quantity = new_quantity
    else:
        cart_item = Cart(
            user_id=user.id,
            product_id=product.id,
            quantity=data['quantity']
        )
        db.session.add(cart_item)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Product added to cart',
            'cart_item_id': cart_item.id,
            'quantity': cart_item.quantity
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Test Data Population
def populate_test_data():
    with app.app_context():
        # Create test user
        if not User.query.get(1):
            user = User(id=1, username='testuser')
            db.session.add(user)
        
        # Create test products
        products = [
            Product(id=1, name='Laptop', price=999.99, stock=10),
            Product(id=2, name='Phone', price=699.99, stock=15),
        ]
        for p in products:
            if not Product.query.get(p.id):
                db.session.add(p)
        
        db.session.commit()

if __name__ == '__main__':
    populate_test_data()
    app.run(debug=True)