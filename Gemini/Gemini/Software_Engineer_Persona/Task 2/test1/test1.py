from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Replace with your DB URI
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Assuming user_id is available
    quantity = db.Column(db.Integer, nullable=False)

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.serialize())
    return jsonify({'error': 'Product not found'}), 404

Product.serialize = lambda self: {
    'id': self.id,
    'name': self.name,
    'price': self.price,
    'stock': self.stock
}

@app.route('/carts/<int:user_id>/add', methods=['POST'])
def add_to_cart(user_id):
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity')

    product = Product.query.get(product_id)
    if not product or product.stock < quantity:
        return jsonify({'error': 'Product not found or insufficient stock'}), 400

    cart_item = CartItem(product_id=product_id, user_id=user_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Insert sample product data
        product1 = Product(name="Product A", price=10.99, stock=5)
        product2 = Product(name="Product B", price=19.99, stock=10)
        db.session.add(product1)
        db.session.add(product2)
        db.session.commit()  # Commit the product changes first

        # Insert a sample cart item
        cart_item = CartItem(product_id=product1.id, user_id=1, quantity=3)  # Assuming user_id 1 exists
        db.session.add(cart_item)

        db.session.commit()
    app.run(debug=True)