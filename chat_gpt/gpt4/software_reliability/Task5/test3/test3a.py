from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Define Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)

# Initialize the database
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

    # Add sample data for testing
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', is_admin=True)
        normal_user = User(username='user1', is_admin=False)
        db.session.add(admin_user)
        db.session.add(normal_user)
        db.session.commit()

    if not Product.query.first():
        sample_product = Product(name='Sample Product', description='This is a sample product.', price=19.99)
        db.session.add(sample_product)
        db.session.commit()

# Helper function to check if the user is admin
def check_admin(username):
    user = User.query.filter_by(username=username).first()
    if user and user.is_admin:
        return True
    return False

# Route to add a new product
@app.route('/products', methods=['POST'])
def add_product():
    username = request.headers.get('username')
    if not check_admin(username):
        return abort(403, 'Admin privileges required')

    data = request.get_json()
    new_product = Product(name=data['name'], description=data.get('description'), price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added successfully'}), 201

# Route to update an existing product
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    username = request.headers.get('username')
    if not check_admin(username):
        return abort(403, 'Admin privileges required')

    data = request.get_json()
    product = Product.query.get_or_404(product_id)
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})

# Route to delete a product
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    username = request.headers.get('username')
    if not check_admin(username):
        return abort(403, 'Admin privileges required')

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

# Route to view all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description, 'price': p.price} for p in products])

if __name__ == '__main__':
    app.run(debug=True)