from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField
from wtforms.validators import DataRequired

# Assuming you have a function to get the current user's data
def get_current_user():
    # ...

def has_admin_privileges(user):
    return user.role == 'admin'

# Decorator to check for admin privileges
def require_admin(view):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not has_admin_privileges(user):
            # Handle unauthorized access (e.g., redirect to login)
            return redirect('/login')
        return view(*args, **kwargs)
    return wrapper

app = Flask(__name__)
# ... CSRF protection configuration

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired()])

@app.route('/admin/products')
@require_admin
def admin_products():
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@require_admin
def admin_product_add():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('admin_products'))
    return render_template('admin_product_add.html', form=form)

# ... similar views for editing and deleting