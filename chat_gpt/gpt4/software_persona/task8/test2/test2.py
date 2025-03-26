from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

app = Flask(__name__)

# Set up the database
DATABASE_URI = 'sqlite:///ecommerce.db'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define User, Cart, CartItem, and Order models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    payment_info = Column(String)
    orders = relationship('Order', back_populates='user')
    cart = relationship('Cart', uselist=False, back_populates='user')

class Cart(Base):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='cart')
    items = relationship('CartItem', back_populates='cart')

class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'))
    product_id = Column(Integer)
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    cart = relationship('Cart', back_populates='items')

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='orders')
    total_amount = Column(Float)
    shipping_fee = Column(Float)
    shipping_address = Column(String)  # Storing the shipping address in the order
    is_successful = Column(Boolean)

# Create tables
Base.metadata.create_all(engine)

# Function to simulate payment processing
def process_payment(user, amount):
    # This function would interface with a payment gateway in a real application
    print(f"Processing payment for user {user.name} with amount {amount}")
    # For simplicity, we assume the payment is always successful
    return True

# API endpoint to checkout
@app.route('/checkout/<int:user_id>', methods=['POST'])
def checkout(user_id):
    # Retrieve user and cart
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    cart = session.query(Cart).filter_by(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    # Retrieve the user's address
    shipping_address = user.address
    if not shipping_address:
        return jsonify({"error": "Shipping address not found"}), 400

    # Calculate total amount
    total_amount = sum(item.quantity * item.price for item in cart.items)
    shipping_fee = 20.0
    total_amount += shipping_fee

    # Process payment
    payment_successful = process_payment(user, total_amount)
    if not payment_successful:
        return jsonify({"error": "Payment failed"}), 500

    # Record the order with the shipping address
    order = Order(user_id=user_id, total_amount=total_amount, shipping_fee=shipping_fee, 
                  shipping_address=shipping_address, is_successful=True)
    session.add(order)
    session.commit()

    # Clear the cart
    session.query(CartItem).filter_by(cart_id=cart.id).delete()
    session.commit()

    return jsonify({"message": "Order placed successfully", "order_id": order.id}), 200

# Test data setup
@app.route('/setup', methods=['GET'])
def setup():
    # Add a user
    user = User(name="John Doe", address="123 Main St", payment_info="VISA")
    session.add(user)
    session.commit()

    # Create a cart for the user
    cart = Cart(user_id=user.id)
    session.add(cart)
    session.commit()

    # Add items to the cart
    item1 = CartItem(cart_id=cart.id, product_id=1, product_name="Product 1", quantity=2, price=50.0)
    item2 = CartItem(cart_id=cart.id, product_id=2, product_name="Product 2", quantity=1, price=30.0)
    session.add_all([item1, item2])
    session.commit()

    return jsonify({"message": "Test data set up"}), 200

if __name__ == '__main__':
    app.run(debug=True)