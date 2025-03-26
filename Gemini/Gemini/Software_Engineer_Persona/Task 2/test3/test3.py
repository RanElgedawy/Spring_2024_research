import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///your_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock
        }

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize()) 

    return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/<int:user_id>/add', 
 methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400

    cart_item = CartItem.query.filter_by(product_id=product_id, user_id=user_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(product_id=product_id, user_id=user_id, quantity=quantity)
        db.session.add(cart_item)

    product.stock -= quantity
    db.session.commit()

    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Insert test products
        products = [
            Product(name='Product A', price=19.99, stock=10),
            Product(name='Product B', price=29.99, stock=5),
            Product(name='Product C', price=9.99, stock=20)
        ]
        db.session.add_all(products)

        # Insert test cart items
        cart_items = [
            CartItem(product_id=1, user_id=1, quantity=2),
            CartItem(product_id=2, user_id=2, quantity=3)
        ]
        db.session.add_all(cart_items)

        db.session.commit()
    app.run(debug=True)