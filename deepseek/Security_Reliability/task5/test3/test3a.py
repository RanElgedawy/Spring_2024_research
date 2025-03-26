# app.py (Backend)
from flask import Flask, request, jsonify, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import html

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CSRF Protection Setup
@app.before_request
def csrf_protect():
    if request.method in ['POST', 'PUT', 'DELETE']:
        token = session.pop('_csrf_token', None)
        if not token or token != request.headers.get('X-CSRF-Token'):
            return jsonify({'error': 'CSRF token mismatch'}), 403

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_password_hash(app.secret_key)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

# Security Decorators
def admin_required(f):
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Product Routes
@app.route('/products', methods=['POST'])
@admin_required
def create_product():
    try:
        data = request.get_json()
        # Input validation and sanitization
        name = html.escape(data['name'].strip())
        description = html.escape(data.get('description', '').strip())
        price = float(data['price'])
        stock = int(data.get('stock', 0))

        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product created', 'id': product.id}), 201
    except (KeyError, ValueError) as e:
        return jsonify({'error': 'Invalid input'}), 400

@app.route('/products/<int:id>', methods=['PUT', 'DELETE'])
@admin_required
def manage_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.get_json()
        # Update and sanitize fields
        product.name = html.escape(data.get('name', product.name).strip())
        product.description = html.escape(data.get('description', product.description).strip())
        try:
            product.price = float(data.get('price', product.price))
            product.stock = int(data.get('stock', product.stock))
        except ValueError:
            return jsonify({'error': 'Invalid numeric value'}), 400
        db.session.commit()
        return jsonify({'message': 'Product updated'})
    elif request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted'})

# Test Routes
@app.route('/test/setup')
def test_setup():
    db.drop_all()
    db.create_all()
    admin = User(username='admin', is_admin=True)
    db.session.add(admin)
    db.session.commit()
    session['user_id'] = admin.id
    return jsonify({'message': 'Test setup complete'})

@app.route('/test/interface')
def test_interface():
    return render_template_string('''
        <h1>Admin Test Interface</h1>
        <script>
        const csrfToken = "{{ csrf_token() }}";
        
        async function createProduct() {
            const response = await fetch('/products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    name: 'Test Product',
                    price: 9.99,
                    stock: 10
                })
            });
            alert(await response.text());
        }
        </script>
        <button onclick="createProduct()">Test Create Product</button>
    ''')

if __name__ == '__main__':
    app.run(debug=True)