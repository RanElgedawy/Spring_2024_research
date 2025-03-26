from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(255))
    stock = db.Column(db.Integer)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)

# Assuming you have a User model and login management setup

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize())
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if product and product.stock > 0:
        cart_item = CartItem(product_id=product_id, user_id=current_user.id, quantity=1)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Product added to cart'})
    else:
        return jsonify({'error': 'Product not available or out of stock'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)