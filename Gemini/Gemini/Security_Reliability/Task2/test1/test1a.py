from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://your_user:your_password@your_host/your_database'
db = SQLAlchemy(app)

class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    price = db.Column(db.Decimal(10, 2))
    quantity = db.Column(db.Integer)

# ... similar models for User, Cart, and CartItem

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/<int:user_id>/items', methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    product = Product.query.get(product_id)
    if product and product.quantity > 0:
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
        cart_item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Product added to cart'})
    return jsonify({'error': 'Product not available or out of stock'}), 400

# ... other endpoints

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)