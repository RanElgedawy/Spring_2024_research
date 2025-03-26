from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

# Define Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

# Define User model (Assuming there is a User model)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Route to add a new product (admin only)
@app.route('/product/add', methods=['POST'])
def add_product():
    with app.app_context():  # Ensure code is executed within the application context
        data = request.get_json()
        user_id = data.get('user_id')
        # Check if the user is an admin
        user = User.query.filter_by(id=user_id).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'You do not have admin privileges'}), 401
        # Add the product
        product = Product(name=data['name'], price=data['price'], description=data.get('description'))
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully'}), 201

# Route to update a product (admin only)
@app.route('/product/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    with app.app_context():
        data = request.get_json()
        user_id = data.get('user_id')
        # Check if the user is an admin
        user = User.query.filter_by(id=user_id).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'You do not have admin privileges'}), 401
        # Update the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.description = data.get('description', product.description)
        db.session.commit()
        return jsonify({'message': 'Product updated successfully'}), 200

# Route to delete a product (admin only)
@app.route('/product/delete/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    with app.app_context():
        user_id = request.args.get('user_id')
        # Check if the user is an admin
        user = User.query.filter_by(id=user_id).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'You do not have admin privileges'}), 401
        # Delete the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200

# Route to create a new user with admin privileges
@app.route('/user/create', methods=['POST'])
def create_user():
    with app.app_context():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        is_admin = data.get('is_admin', False)  # Default to False if not provided
        # Create the user
        user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201

if __name__ == '__main__':
    with app.app_context():  # Ensure code is executed within the application context
        # Create tables if they do not exist
        db.create_all()
    app.run(debug=True)