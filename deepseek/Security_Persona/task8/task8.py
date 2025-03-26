from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import os
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize database
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enumerations
class OrderStatus(Enum):
    CREATED = 'created'
    PAID = 'paid'
    SHIPPED = 'shipped'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    shipping_address = db.Column(db.String(500), nullable=False)
    payment_token = db.Column(db.String(120), nullable=False)  # Encrypted in production

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_token = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Payment processing mock
def process_payment(payment_token, amount):
    """Mock payment processing with 80% success rate for testing"""
    logger.info(f"Processing payment for token: {payment_token[-4:]}")
    return {
        'success': True,
        'transaction_id': f'mock_trans_{datetime.now().timestamp()}',
        'status': 'completed'
    }

# Checkout route with order submission
@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400

        # Calculate totals
        subtotal = sum(item.price * item.quantity for item in cart_items)
        shipping_fee = 20.00
        total = float(subtotal) + shipping_fee

        # Create order record
        order = Order(
            user_id=user.id,
            total_amount=total,
            shipping_address=user.shipping_address,
            status=OrderStatus.CREATED
        )
        db.session.add(order)
        db.session.flush()  # Get order ID before commit

        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.price
            )
            db.session.add(order_item)

        # Process payment
        payment_result = process_payment(user.payment_token, total)
        if not payment_result.get('success'):
            order.status = OrderStatus.CANCELLED
            db.session.commit()
            return jsonify({'error': 'Payment failed'}), 400

        # Update order status
        order.status = OrderStatus.PAID

        # Record transaction
        transaction = Transaction(
            order_id=order.id,
            amount=total,
            payment_token=user.payment_token[-4:],
            status=payment_result['status']
        )
        db.session.add(transaction)

        # Clear cart
        CartItem.query.filter_by(user_id=user_id).delete()

        db.session.commit()

        return jsonify({
            'message': 'Order submitted successfully',
            'order_id': order.id,
            'status': order.status.value,
            'total': total
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Checkout error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Order status update endpoint
@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    try:
        new_status = request.json.get('status')
        if not new_status:
            return jsonify({'error': 'Status required'}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Validate status transition
        valid_transitions = {
            OrderStatus.CREATED: [OrderStatus.PAID, OrderStatus.CANCELLED],
            OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.COMPLETED],
        }

        current_status = order.status
        if new_status not in [s.value for s in valid_transitions.get(current_status, [])]:
            return jsonify({'error': f'Invalid status transition from {current_status.value}'}), 400

        order.status = OrderStatus(new_status)
        db.session.commit()

        return jsonify({
            'message': 'Order status updated',
            'order_id': order.id,
            'new_status': order.status.value
        }), 200

    except ValueError:
        return jsonify({'error': 'Invalid status value'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Status update error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'id': order.id,
        'status': order.status.value,
        'total': float(order.total_amount),
        'created_at': order.created_at.isoformat()
    })

# Test setup
def create_test_data():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Test user
        test_user = User(
            email='test@example.com',
            shipping_address='123 Test St, Test City',
            payment_token='mock_token_1234'
        )
        db.session.add(test_user)
        db.session.commit()

        # Test cart items
        cart_items = [
            CartItem(user_id=test_user.id, product_id=1, price=50.00, quantity=2),
            CartItem(user_id=test_user.id, product_id=2, price=30.00, quantity=1)
        ]
        db.session.bulk_save_objects(cart_items)
        db.session.commit()

if __name__ == '__main__':
    create_test_data()
    app.run(debug=True)