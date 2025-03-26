from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Add other user fields as needed

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    # Add other product fields as needed

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db.init_app(app)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize()) 

    return jsonify({'error': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.json.get('product_id')
    product = Product.query.get(product_id)
    if product and product.stock > 0:
        user = User.query.get(current_user.id)
        cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 
 'Product added to cart'})
    return jsonify({'error': 'Product not found or out of stock'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)