from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Replace with your desired DB URI
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

class CartItem(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'))
    user_id = db.Column(db.String(36))  # Assuming user IDs are stored
    quantity = db.Column(db.Integer)

@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.json())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/<user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    product = Product.query.get(product_id)
    if not product or product.stock <= 0:
        return jsonify({'error': 'Product not available or out of stock'}), 400

    cart_item = CartItem(id=str(uuid.uuid4()), product_id=product_id, user_id=user_id, quantity=1)
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)