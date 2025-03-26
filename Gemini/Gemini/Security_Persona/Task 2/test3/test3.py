from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100)) 
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer) 

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity
        }


class CartItem(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
     product_id = db.Column(db.Integer, db.ForeignKey('product.id')) 

     quantity = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))

SQLALCHEMY_DATABASE_URI = 'sqlite:///ecommerce.db'  # Replace with your desired database URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config.from_object('config')
db.init_app(app)

# API endpoints
@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.to_dict())  

    return jsonify({'message': 'Product not found'}), 404

@app.route('/carts/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    product = Product.query.get(product_id)
    if not product or product.quantity < quantity:
        return jsonify({'message': 'Product is out of stock or invalid'}), 400

    cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'Product added to cart'})

# ... other API endpoints for cart management, user authentication, etc.

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create test users
        user1 = User(username='user1')
        user2 = User(username='user2')
        db.session.add_all([user1, user2])

        # Create test products
        product1 = Product(name='Product 1', price=19.99, quantity=10)
        product2 = Product(name='Product 2', price=29.99, quantity=5)
        db.session.add_all([product1, product2])

        # Add products to carts
        cart_item1 = CartItem(user_id=user1.id, product_id=product1.id, quantity=2)
        cart_item2 = CartItem(user_id=user2.id, product_id=product2.id, quantity=3)
        db.session.add_all([cart_item1, cart_item2])

        db.session.commit()
    app.run(debug=True)