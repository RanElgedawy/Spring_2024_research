from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model with admin flag
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)

# For loading a user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function to check if current user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("You need to be an admin to access this page.")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        new_product = Product(name=name, description=description, price=price)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully.")
        return redirect(url_for('admin_products'))
    return render_template('add_product.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get(id)
    if not product:
        flash("Product not found.")
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        db.session.commit()
        flash("Product updated successfully.")
        return redirect(url_for('admin_products'))

    return render_template('edit_product.html', product=product)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        flash("Product not found.")
        return redirect(url_for('admin_products'))

    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully.")
    return redirect(url_for('admin_products'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            flash('Login successful.')
            return redirect(url_for('admin_products'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return "Welcome to the e-commerce site!"

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.drop_all()
        db.create_all()
        user1 = User(username='regularuser', password='password123', is_admin=False)
        admin_user = User(username='adminuser', password='adminpass', is_admin=True)

        db.session.add(user1)
        db.session.add(admin_user)
        db.session.commit()

    app.run(debug=True)