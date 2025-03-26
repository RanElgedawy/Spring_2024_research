from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Set up the database with SQLite
DATABASE_URL = 'sqlite:///ecommerce.db'
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Product model
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

# Cart model
class Cart(Base):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    product = relationship('Product')

# Create the tables in the database
Base.metadata.create_all(engine)

# Set up the session
Session = sessionmaker(bind=engine)
session = Session()

# API endpoint to retrieve product by ID
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = session.query(Product).filter_by(id=product_id).first()
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock
        })
    return jsonify({'error': 'Product not found'}), 404

# API endpoint to add product to cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    # Check if the product exists and is in stock
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'error': 'Not enough stock'}), 400

    # Add product to the cart
    try:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        session.add(cart_item)
        product.stock -= quantity  # Update stock
        session.commit()
        return jsonify({'message': 'Product added to cart'}), 201
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'Failed to add to cart'}), 500

# API endpoint to get the user's cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    cart_items = session.query(Cart).filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 404

    cart = []
    for item in cart_items:
        cart.append({
            'product_id': item.product_id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity
        })
    return jsonify(cart), 200

if __name__ == '__main__':
    app.run(debug=True)