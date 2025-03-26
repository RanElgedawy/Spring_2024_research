from flask import Flask, render_template_string, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DecimalField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change to a secure random key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)

# Create tables if they don't exist
with app.app_context():
    db.drop_all()
    db.create_all()
    # Create a default admin user if one doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', is_admin=True)
        db.session.add(admin_user)
        db.session.commit()

# Simulate a logged-in user (in production use a proper authentication system)
def get_current_user():
    # For demonstration, always return the admin user.
    return User.query.filter_by(username='admin').first()

# Decorator to require admin privileges
def admin_required(f):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            abort(403, description="Admin privileges required.")
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Forms using Flask-WTF (CSRF is automatically included)
class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

# Templates defined inline for simplicity (Jinja2 auto-escapes by default)
admin_template = """
<!doctype html>
<title>Admin Product Management</title>
<h1>Product Management</h1>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color: red;">
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<h2>Add New Product</h2>
<form method="POST" action="{{ url_for('add_product') }}">
    {{ form.hidden_tag() }}
    <p>
        {{ form.name.label }}<br>
        {{ form.name(size=40) }}
    </p>
    <p>
        {{ form.description.label }}<br>
        {{ form.description(rows=3, cols=40) }}
    </p>
    <p>
        {{ form.price.label }}<br>
        {{ form.price(step="0.01") }}
    </p>
    <p>{{ form.submit() }}</p>
</form>
<hr>
<h2>Existing Products</h2>
<ul>
  {% for product in products %}
    <li>
      <strong>{{ product.name }}</strong> - ${{ product.price }}<br>
      {{ product.description }}<br>
      <a href="{{ url_for('edit_product', product_id=product.id) }}">Edit</a> | 
      <form method="POST" action="{{ url_for('delete_product', product_id=product.id) }}" style="display:inline;">
          {{ form.hidden_tag() }}
          <button type="submit" onclick="return confirm('Are you sure you want to delete this product?');">Delete</button>
      </form>
    </li>
  {% else %}
    <li>No products available.</li>
  {% endfor %}
</ul>
"""

edit_template = """
<!doctype html>
<title>Edit Product</title>
<h1>Edit Product</h1>
<form method="POST">
    {{ form.hidden_tag() }}
    <p>
        {{ form.name.label }}<br>
        {{ form.name(size=40) }}
    </p>
    <p>
        {{ form.description.label }}<br>
        {{ form.description(rows=3, cols=40) }}
    </p>
    <p>
        {{ form.price.label }}<br>
        {{ form.price(step="0.01") }}
    </p>
    <p>{{ form.submit() }}</p>
</form>
<p><a href="{{ url_for('admin_products') }}">Back to Product List</a></p>
"""

# Routes for admin product management
@app.route('/admin/products', methods=['GET'])
@admin_required
def admin_products():
    products = Product.query.all()
    form = ProductForm()
    return render_template_string(admin_template, form=form, products=products)

@app.route('/admin/products/add', methods=['POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!")
    else:
        flash("Failed to add product. Please check the input.")
    return redirect(url_for('admin_products'))

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if request.method == 'POST' and form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        db.session.commit()
        flash("Product updated successfully!")
        return redirect(url_for('admin_products'))
    return render_template_string(edit_template, form=form)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!")
    return redirect(url_for('admin_products'))

if __name__ == '__main__':
    app.run(debug=True)
