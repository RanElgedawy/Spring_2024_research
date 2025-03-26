from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    # In a real application, you would store hashed passwords
    password = Column(String(120), nullable=False)
    carts = relationship('Cart', back_populates='user')

class Product(db.Model):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(String(255))
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

class Cart(db.Model):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(db.DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='carts')
    product = relationship('Product')

    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)

# --- API Endpoints ---

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock
    })

@app.route('/cart', methods=['POST'])
def add_to_cart():
    # In a real application, you would get the user ID from the session or token
    user_id = request.form.get('user_id')
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1, type=int)

    if not user_id or not product_id:
        return jsonify({'error': 'Missing user_id or product_id'}), 400

    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'error': f'Not enough stock. Only {product.stock} available.'}), 400

    # Check if the product is already in the user's cart
    existing_cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing_cart_item:
        existing_cart_item.quantity += quantity
        db.session.commit()
        return jsonify({'message': f'{quantity} more of {product.name} added to cart.'}), 200
    else:
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)
        db.session.commit()
        return jsonify({'message': f'{product.name} added to cart.'}), 201

# --- Helper function to create and populate the database ---
def create_and_populate_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Add some sample users
        user1 = User(username='john_doe', password='password123')
        user2 = User(username='jane_smith', password='secure_pass')
        db.session.add_all([user1, user2])
        db.session.commit()

        # Add some sample products
        product1 = Product(name='Laptop', description='High-performance laptop', price=1200.00, stock=10)
        product2 = Product(name='Mouse', description='Wireless ergonomic mouse', price=25.00, stock=50)
        product3 = Product(name='Keyboard', description='Mechanical gaming keyboard', price=75.00, stock=0)
        db.session.add_all([product1, product2, product3])
        db.session.commit()

        print("Database created and populated with sample data.")

# --- Main execution block ---
if __name__ == '__main__':
    create_and_populate_db()
    app.run(debug=True)