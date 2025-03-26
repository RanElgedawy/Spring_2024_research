from flask import Flask, render_template_string, request, redirect, url_for, session, abort, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DecimalField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_should_be_changed'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Define database models.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)

# Create tables and add a demo admin user if they do not exist.
@app.before_first_request
def setup_db():
    db.drop_all()
    db.create_all()
    # Create a demo admin user if not exists.
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
    # Optionally, add a sample product.
    if not Product.query.first():
        sample = Product(name='Sample Product', description='This is a sample product.', price=9.99)
        db.session.add(sample)
        db.session.commit()

# Simple login simulation: this route “logs in” the admin.
@app.route('/login_admin')
def login_admin():
    admin = User.query.filter_by(username='admin').first()
    session['user_id'] = admin.id
    flash('Logged in as admin.', 'info')
    return redirect(url_for('list_products'))

# Decorator to ensure the user is an admin.
def admin_required(func):
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('You must be logged in as admin to access this page.', 'warning')
            return redirect(url_for('login_admin'))
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# WTForms form for product details.
class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

# Template for listing products.
list_template = """
<!doctype html>
<title>Products</title>
<h1>Products</h1>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <ul>
    {% for category, message in messages %}
      <li>{{ category }}: {{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<table border="1">
<tr>
    <th>ID</th>
    <th>Name</th>
    <th>Description</th>
    <th>Price</th>
    <th>Actions</th>
</tr>
{% for product in products %}
<tr>
    <td>{{ product.id }}</td>
    <td>{{ product.name }}</td>
    <td>{{ product.description }}</td>
    <td>{{ product.price }}</td>
    <td>
        <a href="{{ url_for('edit_product', product_id=product.id) }}">Edit</a> |
        <a href="{{ url_for('delete_product', product_id=product.id) }}" onclick="return confirm('Are you sure?');">Delete</a>
    </td>
</tr>
{% endfor %}
</table>
<br>
<a href="{{ url_for('add_product') }}">Add New Product</a>
"""

# Route to list products.
@app.route('/admin/products')
@admin_required
def list_products():
    products = Product.query.all()
    return render_template_string(list_template, products=products)

# Template for add/edit product.
form_template = """
<!doctype html>
<title>{{ title }}</title>
<h1>{{ title }}</h1>
<form method="post">
    {{ form.hidden_tag() }}
    <p>
        {{ form.name.label }}<br>
        {{ form.name(size=40) }}
    </p>
    <p>
        {{ form.description.label }}<br>
        {{ form.description(rows=5, cols=40) }}
    </p>
    <p>
        {{ form.price.label }}<br>
        {{ form.price() }}
    </p>
    <p>{{ form.submit() }}</p>
</form>
<a href="{{ url_for('list_products') }}">Back to Products</a>
"""

# Route to add a product.
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('list_products'))
    return render_template_string(form_template, form=form, title="Add Product")

# Route to edit a product.
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('list_products'))
    return render_template_string(form_template, form=form, title="Edit Product")

# Route to delete a product.
@app.route('/admin/delete/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # For additional safety, you might include a confirmation form.
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('list_products'))

if __name__ == '__main__':
    # Set the environment variable to avoid caching issues with the templates.
    os.environ['FLASK_ENV'] = 'development'
    app.run(debug=True)
