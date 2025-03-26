from flask import Flask, request, render_template_string, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from markupsafe import escape
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Admin verification decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return "Unauthorized", 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Product management routes
@app.route('/add-product', methods=['GET', 'POST'])
@admin_required
@csrf.exempt  # Remove this line in real deployment
def add_product():
    if request.method == 'POST':
        try:
            # Sanitize input to prevent XSS
            name = escape(request.form['name'])
            description = escape(request.form['description'])
            price = float(request.form['price'])
            
            new_product = Product(
                name=name,
                description=description,
                price=price
            )
            db.session.add(new_product)
            db.session.commit()
            return "Product added successfully!"
        except ValueError:
            return "Invalid price format", 400
    
    # CSRF token included in form
    return render_template_string('''
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            Name: <input type="text" name="name" required><br>
            Description: <textarea name="description" required></textarea><br>
            Price: <input type="number" step="0.01" name="price" required><br>
            <button type="submit">Add Product</button>
        </form>
    ''')

@app.route('/edit-product/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        try:
            product.name = escape(request.form['name'])
            product.description = escape(request.form['description'])
            product.price = float(request.form['price'])
            db.session.commit()
            return "Product updated successfully!"
        except ValueError:
            return "Invalid price format", 400

    return render_template_string('''
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            Name: <input type="text" name="name" value="{{ product.name }}" required><br>
            Description: <textarea name="description" required>{{ product.description }}</textarea><br>
            Price: <input type="number" step="0.01" name="price" value="{{ product.price }}" required><br>
            <button type="submit">Update Product</button>
        </form>
    ''', product=product)

@app.route('/delete-product/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return "Product deleted successfully"

# Test routes
@app.route('/create-test-admin')
def create_test_admin():
    test_admin = User(username='admin', is_admin=True)
    db.session.add(test_admin)
    db.session.commit()
    return "Test admin created"

@app.route('/login-test-admin')
def login_test_admin():
    admin = User.query.filter_by(username='admin').first()
    session['user_id'] = admin.id
    return "Logged in as test admin"

if __name__ == '__main__':
    app.run(debug=True)