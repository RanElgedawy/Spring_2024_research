import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'sqlite:///ecommerce.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)  # In production, use proper key management

db = SQLAlchemy(app)

# Mock Payment Processor (Replace with real payment gateway SDK in production)
class MockPaymentProcessor:
    def process_payment(self, token, amount):
        # In real implementation, use Stripe/Braintree/etc. with proper error handling
        return {'success': True, 'transaction_id': 'mock_txn_123'}

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    payment_token = db.Column(db.String(255))  # Stored payment method token (PCI compliant)
    cart = relationship('Cart', backref='user', uselist=False)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    items = relationship('CartItem', backref='cart')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.Column(db.Text, nullable=False)  # JSON string of purchased items

# Security Helper Functions
def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + key

def verify_password(stored_hash, password):
    salt = stored_hash[:32]
    key = stored_hash[32:]
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return new_key == key

# Checkout Route
@app.route('/checkout', methods=['POST'])
def checkout():
    # Authentication check
    auth = request.authorization
    if not auth or not verify_user_credentials(auth.username, auth.password):
        return jsonify({'error': 'Authentication required'}), 401

    user = User.query.filter_by(email=auth.username).first()
    if not user or not user.cart:
        return jsonify({'error': 'User or cart not found'}), 404

    # Calculate total
    total = sum(item.price * item.quantity for item in user.cart.items)
    total += 20  # Shipping fee

    # Process payment
    payment_processor = MockPaymentProcessor()
    result = payment_processor.process_payment(user.payment_token, total)
    
    if not result['success']:
        return jsonify({'error': 'Payment failed'}), 400

    # Record transaction
    try:
        transaction = Transaction(
            user_id=user.id,
            amount=total,
            items=str([{'product_id': item.product_id, 'quantity': item.quantity} 
                       for item in user.cart.items])
        )
        db.session.add(transaction)
        
        # Clear cart
        CartItem.query.filter_by(cart_id=user.cart.id).delete()
        db.session.commit()
        return jsonify({'message': 'Checkout successful', 'transaction_id': transaction.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def verify_user_credentials(email, password):
    user = User.query.filter_by(email=email).first()
    return user and verify_password(user.password_hash, password)

# Test Route
@app.route('/test_checkout', methods=['POST'])
def test_checkout():
    # Setup test user and cart
    test_user = User(
        email='test@example.com',
        password_hash=hash_password('test123'),
        shipping_address='123 Test St',
        payment_token='valid_token'
    )
    test_cart = Cart(user=test_user)
    test_cart.items = [
        CartItem(product_id=1, quantity=2, price=19.99),
        CartItem(product_id=2, quantity=1, price=49.99)
    ]
    
    db.session.add(test_user)
    db.session.commit()
    
    # Perform test checkout
    auth = ('test@example.com', 'test123')
    response = app.test_client().post(
        '/checkout',
        headers={'Authorization': 'Basic ' + base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()}
    )
    
    # Cleanup
    db.session.delete(test_user)
    db.session.commit()
    
    return response

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=False)  # Always set debug=False in production