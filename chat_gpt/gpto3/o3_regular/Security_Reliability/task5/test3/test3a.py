from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# ----- Database Models -----
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)

# ----- WTForms for Products -----
class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    price = DecimalField('Price', validators=[DataRequired()])
    submit = SubmitField('Submit')

# ----- Admin Authorization Decorator -----
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verify that the logged in user is admin.
        user_id = session.get('user_id')
        if not user_id:
            flash("Please log in as an admin to access this page.")
            return redirect(url_for('login'))
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ----- Routes -----
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    A simple login simulation.
    To test, log in with the username "admin" (this user is created automatically).
    """
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
            flash(f"Logged in successfully as {user.username}")
            return redirect(url_for('list_products'))
        else:
            flash("User not found.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out.")
    return redirect(url_for('login'))

@app.route('/')
def list_products():
    products = Product.query.all()
    return render_template('list_products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # SQLAlchemy uses parameterized queries to avoid SQL injection.
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=float(form.price.data)
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added successfully.")
        return redirect(url_for('list_products'))
    return render_template('product_form.html', form=form, action="Add")

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = float(form.price.data)
        db.session.commit()
        flash("Product updated successfully.")
        return redirect(url_for('list_products'))
    return render_template('product_form.html', form=form, action="Edit")

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully.")
    return redirect(url_for('list_products'))

# ----- Database Initialization -----
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()
    # Create a test admin user if one doesn't exist.
    if not User.query.filter_by(username="admin").first():
        admin_user = User(username="admin", is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
    # Add a sample product if the database is empty.
    if not Product.query.first():
        sample_product = Product(name="Sample Product", description="This is a sample product.", price=9.99)
        db.session.add(sample_product)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
