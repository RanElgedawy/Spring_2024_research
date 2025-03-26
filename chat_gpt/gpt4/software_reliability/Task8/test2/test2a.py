from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuring the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Defining the User, Cart, and Order models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.String(200), nullable=False)

# Create tables
db.drop_all()
db.create_all()

@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.json.get('user_id')
    
    # Retrieve user details
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Retrieve cart items for the user
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate the total amount
    total_amount = sum(item.price * item.quantity for item in cart_items) + 20  # Adding $20 shipping fee

    # Simulate a successful payment (you can replace this with real payment logic)
    payment_success = True  # In real scenario, call payment gateway

    if payment_success:
        # Record the order in the Order table
        new_order = Order(
            user_id=user.id,
            total_amount=total_amount,
            status='success',
            shipping_address=user.address
        )
        db.session.add(new_order)
        db.session.commit()

        # Clear the cart after successful order
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        return jsonify({
            'message': 'Order placed successfully',
            'order_id': new_order.id,
            'total_amount': total_amount,
            'shipping_address': user.address
        }), 200
    else:
        return jsonify({'error': 'Payment failed'}), 400

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = request.json.get('user_id')
    product_name = request.json.get('product_name')
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')
    price = request.json.get('price')

    cart_item = Cart(user_id=user_id, product_name=product_name, product_id=product_id, quantity=quantity, price=price)
    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'Product added to cart successfully'}), 200

@app.route('/create_user', methods=['POST'])
def create_user():
    name = request.json.get('name')
    email = request.json.get('email')
    address = request.json.get('address')

    new_user = User(name=name, email=email, address=address)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 200

if __name__ == '__main__':
    app.run(debug=True)
