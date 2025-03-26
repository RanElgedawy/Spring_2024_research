from flask import Flask, jsonify, request, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from functools import wraps
import bleach

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'your-secret-key-here',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///ecommerce.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'WTF_CSRF_TIME_LIMIT': 3600
})

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Security Helpers
def sanitize_input(data):
    """Clean user input to prevent XSS"""
    return {
        'name': bleach.clean(data.get('name', '')).strip(),
        'description': bleach.clean(data.get('description', '')).strip(),
        'price': data.get('price'),
        'stock': data.get('stock')
    }

def admin_required(f):
    """Decorator to check admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated

# Product Management Routes
@app.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = sanitize_input(request.get_json())
    
    if not all([data['name'], data['description'], data['price']]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        product = Product(
            name=data['name'],
            description=data['description'],
            price=float(data['price']),
            stock=int(data.get('stock', 0))
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product created', 'id': product.id}), 201
    except ValueError:
        return jsonify({'error': 'Invalid numeric values'}), 400

@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = sanitize_input(request.get_json())
    
    try:
        product.name = data['name'] or product.name
        product.description = data['description'] or product.description
        if 'price' in request.json: 
            product.price = float(data['price'])
        if 'stock' in request.json:
            product.stock = int(data['stock'])
        db.session.commit()
        return jsonify({'message': 'Product updated'})
    except ValueError:
        return jsonify({'error': 'Invalid numeric values'}), 400

@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

# Security Endpoints
@app.route('/csrf-token', methods=['GET'])
def get_csrf():
    return jsonify({'csrf_token': generate_csrf()})

# Testing Interface
@app.route('/test', methods=['GET'])
def test_interface():
    return render_template_string('''
        <html>
            <head>
                <title>Admin Test</title>
                <meta name="csrf-token" content="{{ csrf_token() }}">
            </head>
            <body>
                <h2>Admin Test Interface</h2>
                <div id="messages"></div>
                <button onclick="createAdmin()">Create Test Admin</button>
                <button onclick="createProduct()">Create Test Product</button>
                <script>
                    function log(message) {
                        document.getElementById('messages').innerHTML += `<p>${message}</p>`;
                    }

                    async function createAdmin() {
                        const response = await fetch('/setup-test-admin', {method: 'POST'});
                        const result = await response.json();
                        log(result.message);
                    }

                    async function createProduct() {
                        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
                        const response = await fetch('/products', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify({
                                name: 'Test Product',
                                description: 'Test Description',
                                price: 19.99,
                                stock: 10
                            })
                        });
                        const result = await response.json();
                        log(result.message || result.error);
                    }
                </script>
            </body>
        </html>
    ''')

@app.route('/setup-test-admin', methods=['POST'])
def setup_test_admin():
    """Create test admin user (for demonstration only)"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()
    session['user_id'] = admin.id
    return jsonify({'message': 'Test admin created and logged in'})

if __name__ == '__main__':
    app.run(debug=True)