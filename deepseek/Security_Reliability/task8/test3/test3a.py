# checkout_system.py
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import os
import stripe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')  # In prod, use proper secret management

# Initialize Stripe (test mode)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_4eC39HqLyjWDarjtT1zdp7dc')

db = SQLAlchemy(app)

# Database Models (simplified existing structure)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    payment_token = db.Column(db.String(30))  # Simulated payment method token
    shipping_address = db.Column(db.String(200))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)  # Stored in cents

# Transaction table to create
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer)  # Total amount in cents
    items = db.Column(db.JSON)

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        # Verify authentication
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Retrieve cart items
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        if not cart_items:
            return jsonify({"error": "Cart is empty"}), 400

        # Calculate total
        subtotal = sum(item.price * item.quantity for item in cart_items)
        shipping_fee = 2000  # $20 in cents
        total = subtotal + shipping_fee

        # Process payment
        charge = stripe.Charge.create(
            amount=total,
            currency="usd",
            source=user.payment_token,  # Using stored payment method
            description="E-commerce purchase"
        )

        if charge.status != 'succeeded':
            return jsonify({"error": "Payment failed"}), 402

        # Record transaction
        transaction = Transaction(
            user_id=user.id,
            amount=total,
            items=[{"product_id": item.product_id, "quantity": item.quantity} for item in cart_items]
        )

        # Clear cart and commit transaction
        db.session.add(transaction)
        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        return jsonify({
            "message": "Purchase successful",
            "total": f"${total/100:.2f}",
            "transaction_id": transaction.id
        })

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 500
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500

# Test routes and helpers
@app.route('/test/login', methods=['POST'])
def test_login():
    # Simulate login for testing
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    if user:
        session['user_id'] = user.id
        return jsonify({"message": "Logged in"})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/test/add_to_cart', methods=['POST'])
def add_test_item():
    # Helper to add test items to cart
    if 'user_id' not in session:
        return jsonify({"error": "Login first"}), 401
    
    item = CartItem(
        user_id=session['user_id'],
        product_id=request.json.get('product_id'),
        quantity=request.json.get('quantity'),
        price=request.json.get('price')
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Item added"})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)