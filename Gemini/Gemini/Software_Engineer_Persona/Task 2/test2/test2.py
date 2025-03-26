from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Replace with your DB URI
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock
        }

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    product = db.relationship('Product', backref='cart_items')

# Create database tables if they don't exist
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create some sample products
    product1 = Product(name="Product A", price=19.99, stock=5)
    product2 = Product(name="Product B", price=29.99, stock=0)
    db.session.add_all([product1, product2])
    db.session.commit()

    # Create a sample cart item
    cart_item = CartItem(user_id=1, product_id=product1.id, quantity=2)
    db.session.add(cart_item)
    db.session.commit()

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.json())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/carts/add', methods=['POST'])
def add_to_cart():
    product_id = request.json['product_id']
    user_id = request.json['user_id']  # Assuming user ID is provided

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.stock == 0:
        return jsonify({'error': 'Product out of stock'}), 400

    cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({'message': 'Product added to cart'})

if __name__ == '__main__':
    app.run(debug=True)