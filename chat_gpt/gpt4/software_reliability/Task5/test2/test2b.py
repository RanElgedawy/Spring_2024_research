from flask import Flask, request, jsonify, redirect, url_for, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)

# Create the database tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Sample users for testing (admin and regular user)
with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password=generate_password_hash('admin123'), is_admin=True)
        regular_user = User(username='user', password=generate_password_hash('user123'), is_admin=False)
        db.session.add(admin_user)
        db.session.add(regular_user)
        db.session.commit()

# Route to login user (for testing purposes)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('manage_products'))
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')

# Middleware to check if user is admin
def admin_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return 'Access denied', 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Route to manage products (admin-only)
@app.route('/products', methods=['GET', 'POST'])
@admin_required
def manage_products():
    if request.method == 'POST':
        # Add a new product
        name = request.form['name']
        description = request.form.get('description')
        price = float(request.form['price'])
        new_product = Product(name=name, description=description, price=price)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('manage_products'))
    
    # Display all products
    products = Product.query.all()
    return render_template('products.html', products=products)

# Route to modify a product (admin-only)
@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form.get('description')
        product.price = float(request.form['price'])
        db.session.commit()
        return redirect(url_for('manage_products'))
    return render_template('edit_product.html', product=product)

# Route to delete a product (admin-only)
@app.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('manage_products'))

# Route to logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Templates for testing (login.html, products.html, edit_product.html)
@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)