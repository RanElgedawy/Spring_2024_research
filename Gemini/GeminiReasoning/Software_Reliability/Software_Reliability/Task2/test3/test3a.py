from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DATABASE_URI = 'sqlite:///ecommerce.db'
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    carts = db.relationship('Cart', backref='user', lazy=True)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    carts = db.relationship('Cart', backref='product', lazy=True)

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

# Database Initialization
def initialize_database():
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create tables if they don't exist
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS product (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS cart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES user(user_id),
                FOREIGN KEY (product_id) REFERENCES product(product_id)
            )
        """))
        connection.commit()

    # Add some sample data if the tables are empty
    if session.query(User).count() == 0:
        user1 = User(user_id=1, username='user1')
        user2 = User(user_id=2, username='user2')
        session.add_all([user1, user2])
        session.commit()

    if session.query(Product).count() == 0:
        product1 = Product(product_id=101, name='Laptop', description='High-performance laptop', price=1200.00, stock=10)
        product2 = Product(product_id=102, name='Mouse', description='Wireless optical mouse', price=25.00, stock=50)
        product3 = Product(product_id=103, name='Keyboard', description='Mechanical keyboard', price=75.00, stock=0)
        session.add_all([product1, product2, product3])
        session.commit()

    session.close()

# API Endpoints
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'product_id': product.product_id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock
        })
    return jsonify({'message': 'Product not found'}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not all([user_id, product_id]):
        return jsonify({'message': 'Missing user_id or product_id'}), 400

    user = User.query.get(user_id)
    product = Product.query.get(product_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'message': f'Not enough stock for product {product_id}'}), 400

    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if cart_item:
            cart_item.quantity += quantity
        else:
            new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(new_cart_item)

        product.stock -= quantity
        session.commit()
        return jsonify({'message': f'{quantity} of product {product_id} added to user {user_id}\'s cart'}), 201
    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error adding to cart: {str(e)}'}), 500
    finally:
        session.close()

# Function to test the API
def test_api():
    import requests

    base_url = 'http://127.0.0.1:5000'

    print("\n--- Testing Get Product ---")
    response = requests.get(f'{base_url}/products/101')
    print(f"GET /products/101: {response.status_code} - {response.json()}")

    response = requests.get(f'{base_url}/products/999')
    print(f"GET /products/999: {response.status_code} - {response.json()}")

    print("\n--- Testing Add to Cart ---")
    # Add product 101 (Laptop) to user 1's cart
    payload = {'user_id': 1, 'product_id': 101, 'quantity': 2}
    response = requests.post(f'{base_url}/cart/add', json=payload)
    print(f"POST /cart/add (user 1, product 101, qty 2): {response.status_code} - {response.json()}")

    # Try to add more than available stock
    payload = {'user_id': 1, 'product_id': 101, 'quantity': 10}
    response = requests.post(f'{base_url}/cart/add', json=payload)
    print(f"POST /cart/add (user 1, product 101, qty 10 - should fail): {response.status_code} - {response.json()}")

    # Add product 102 (Mouse) to user 2's cart
    payload = {'user_id': 2, 'product_id': 102, 'quantity': 1}
    response = requests.post(f'{base_url}/cart/add', json=payload)
    print(f"POST /cart/add (user 2, product 102, qty 1): {response.status_code} - {response.json()}")

    # Try to add a product that doesn't exist
    payload = {'user_id': 1, 'product_id': 999, 'quantity': 1}
    response = requests.post(f'{base_url}/cart/add', json=payload)
    print(f"POST /cart/add (user 1, product 999 - should fail): {response.status_code} - {response.json()}")

    # Try to add to a user that doesn't exist
    payload = {'user_id': 99, 'product_id': 101, 'quantity': 1}
    response = requests.post(f'{base_url}/cart/add', json=payload)
    print(f"POST /cart/add (user 99 - should fail): {response.status_code} - {response.json()}")

if __name__ == '__main__':
    initialize_database()
    # To test the API, run this script and then execute the test_api function
    # in a separate Python interpreter or uncomment the line below
    # test_api()
    app.run(debug=True)