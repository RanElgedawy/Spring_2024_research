from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'  # Replace with your DB URI
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity_in_stock = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'quantity_in_stock': self.quantity_in_stock
        }

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'product_id': self.product_id,
            'quantity': self.quantity
        }

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship('CartItem', backref='cart', lazy=True)

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize()) 

    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/<int:user_id>/items', methods=['POST'])
def add_to_cart(user_id):
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

# Validate input and check stock availability
    product = Product.query.get(product_id)
    if not product or product.quantity_in_stock < quantity:
        return jsonify({'error': 'Product is out of stock'}), 400
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)

    cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'Product added to cart'})

@app.route('/carts/<int:user_id>/items')
def get_cart_items(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart:
        return jsonify([item.serialize() for item in cart.items])
    else:
        return jsonify([])
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create some test products
        products = [
            Product(name="Product A", description="This is Product A", price=19.99, quantity_in_stock=10),
            Product(name="Product B", description="This is Product B", price=29.99, quantity_in_stock=5),
            Product(name="Product C", description="This is Product C", price=9.99, quantity_in_stock=0)
        ]

        # Add the products to the database
        db.session.add_all(products)
        db.session.commit()

        print("Test data added successfully.")

    app.run(debug=True)