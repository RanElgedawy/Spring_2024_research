from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import stripe
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    default_card_token = db.Column(db.String)

    # ... other user fields
    address_line1 = db.Column(db.String)
    address_line2 = db.Column(db.String)
    city = db.Column(db.String)
    state = db.Column(db.String)
    zip_code = db.Column(db.String) 
    country = db.Column(db.String)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    status = db.Column(db.String)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship('CartItem') 

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id')) 
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    user_id = data.get('user_id')

    # Retrieve the user's cart and address information
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'})
    
    # Retrieve the user's cart from the database
    cart = Cart.query.filter_by(user_id=user_id).first()

    if not cart:
        return jsonify({'error': 'Cart not found'})

    # Calculate total cost, including shipping fee
    total_cost = sum(item.product.price * item.quantity for item in cart.items) + 20

        # Use the user's address information for shipping
    shipping_address = {
        'line1': user.address_line1,
        'line2': user.address_line2,
        'city': user.city,
        'state': user.state,
        'postal_code': user.zip_code,
        'country': user.country
    }

 # Check if the user is logged in
    if user:
        # Retrieve the user's saved card token
        saved_card_token = user.default_card_token

        # If a saved card is found, use it for payment
        if saved_card_token:
            try:
                charge = stripe.Charge.create(
                    amount=total_cost,
                    currency='usd',
                    source=saved_card_token,
                    description='E-commerce Purchase'
                )
                # ... (rest of the transaction processing)
            except stripe.error.CardError as e:
                return jsonify({'error': e.message})
        # Create a new order
    order = Order(user_id=user_id, total_amount=total_cost)
    db.session.add(order)
    db.session.commit()

    # Update order status to successful if payment is successful
    if charge.status == 'succeeded':
        order.status = 'successful'
        db.session.commit()

    return jsonify({'message': 'Payment successful'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Insert test data
        product = Product(id=1, name="Test Product", price=10.00)  # Adjust name and price as needed
        db.session.add(product)

        user = User(id=1, email="test@example.com")
        db.session.add(user)

        cart = Cart(user_id=1)
        db.session.add(cart)

        cart_item = CartItem(cart_id=1, product_id=1, quantity=2)
        db.session.add(cart_item)
        
        db.session.commit()
    app.run(debug=True)