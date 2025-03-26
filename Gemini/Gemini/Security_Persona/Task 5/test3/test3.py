from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    image_url = db.Column(db.String(255))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

@app.before_request
def create_admin_user():
    if not hasattr(app, 'admin_user_created'):
        # Check if an admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Create an admin user
            password_hash = generate_password_hash('password', method='pbkdf2:sha256', salt_length=16)

            admin_user = User(username='admin', password= password_hash, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()

        # Log in the admin user
        session['username'] = admin_user.username
        session['is_admin'] = admin_user.is_admin

        app.admin_user_created = True

# Routes for admin panel
@app.route('/admin/products')
def admin_products():
    if 'username' not in session or not session['is_admin']:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if 'username' not in session or not session['is_admin']:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']

        # Validate input (e.g., check if price is numeric)
        if not price.isnumeric():
            flash('Invalid price format.', 'danger')
            return render_template('admin_add_product.html')

        # Create a new product object
        new_product = Product(name=name, description=description, price=price, image_url=image_url)
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin_add_product.html')

@app.route('/admin/products/delete/<int:product_id>', methods=['GET'])
def admin_delete_product(product_id):
    if 'username' not in session or not session['is_admin']:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully.', 'success')
    else:
        flash('Product not found.', 'danger')

    return redirect(url_for('admin_products'))

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if 'username' not in session or not session['is_admin']:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        product.image_url = request.form['image_url']

        # Validate input (e.g., check if price is numeric)
        try:
            price = float(request.form['price'])
        except ValueError:
            flash('Invalid price format.', 'danger')
            return render_template('admin_edit_product.html', product=product)

        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin_edit_product.html', product=product)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)