from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db = SQLAlchemy(app)

# Define SQLAlchemy models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# Custom Flask command to clear existing data and populate the database with sample data
def init_db():
    print('Initializing the database with sample data...')
    with app.app_context():
        db.drop_all()  # Drop all existing tables
        db.create_all()

        # Add sample users
        user1 = User(username='user1')
        user2 = User(username='user2')
        db.session.add(user1)
        db.session.add(user2)

        # Add sample products
        product1 = Product(name='Product 1', price=10.99, stock=100)
        product2 = Product(name='Product 2', price=20.49, stock=50)
        db.session.add(product1)
        db.session.add(product2)

        db.session.commit()
    print('Database initialization complete.')

# Initialize the database with sample data
init_db()

# API endpoints
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if product:
            return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'stock': product.stock})
        else:
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': 'An error occurred while retrieving the product'}), 500

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    product = Product.query.get(product_id)
    if product and product.stock >= quantity:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Product added to cart successfully'})
    else:
        return jsonify({'error': 'Product not available or insufficient stock'}), 400

if __name__ == '__main__':
    app.run(debug=True)