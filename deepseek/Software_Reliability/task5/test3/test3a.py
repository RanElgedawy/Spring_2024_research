from flask import Flask, session, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
            
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({"error": "Admin privileges required"}), 403
            
        return f(*args, **kwargs)
    return decorated

# Admin Routes
@app.route('/admin/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    required_fields = ['name', 'price']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            stock=int(data.get('stock', 0))
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added", "id": product.id}), 201
    except ValueError:
        return jsonify({"error": "Invalid price or stock format"}), 400

@app.route('/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
@admin_required
def manage_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        
        try:
            if 'price' in data: product.price = float(data['price'])
            if 'stock' in data: product.stock = int(data['stock'])
        except ValueError:
            return jsonify({"error": "Invalid price or stock format"}), 400
            
        db.session.commit()
        return jsonify({"message": "Product updated"})
        
    elif request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted"})

# Testing Endpoints
@app.route('/test/login/<username>', methods=['GET'])
def test_login(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    session['user_id'] = user.id
    return jsonify({
        "message": "Logged in",
        "user": username,
        "is_admin": user.is_admin
    })

@app.route('/test/user', methods=['POST'])
def create_test_user():
    data = request.get_json()
    if 'username' not in data:
        return jsonify({"error": "Username required"}), 400
        
    user = User(
        username=data['username'],
        is_admin=data.get('is_admin', False)
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({
        "message": "Test user created",
        "id": user.id,
        "is_admin": user.is_admin
    })

if __name__ == '__main__':
    app.run(debug=True)