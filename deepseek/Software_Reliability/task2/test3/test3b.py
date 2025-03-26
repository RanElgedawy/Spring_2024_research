from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='carts')

# Create database tables and sample data
with app.app_context():
    db.drop_all()
    db.create_all()
    if Product.query.count() == 0:
        sample_products = [
            Product(name='Wireless Mouse', price=29.99, stock=10),
            Product(name='Mechanical Keyboard', price=99.99, stock=5),
            Product(name='Gaming Monitor', price=299.99, stock=3)
        ]
        db.session.bulk_save_objects(sample_products)
        db.session.commit()

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
    }), 200

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Missing user ID in headers'}), 400
    
    data = request.get_json()
    if not data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    product_id = data['product_id']
    quantity = data['quantity']
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    # Check if product already in cart
    cart_item = Cart.query.filter_by(
        user_id=user_id, 
        product_id=product_id
    ).first()
    
    try:
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        product.stock -= quantity
        db.session.commit()
        return jsonify({'message': 'Product added to cart successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)