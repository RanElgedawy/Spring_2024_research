from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.csrf import CSRFProtect
import os
from functools import wraps

# Create the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

# Forms
class ProductForm(FlaskForm):
    id = HiddenField("id")
    name = StringField('Product Name', validators=[DataRequired(), Length(max=150)])
    description = StringField('Product Description', validators=[DataRequired(), Length(max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create an instance of LoginForm
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('admin_panel'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    form = ProductForm()
    if form.validate_on_submit():
        if form.id.data:
            product = Product.query.get(form.id.data)
            product.name = form.name.data
            product.description = form.description.data
            product.price = form.price.data
            flash('Product updated successfully')
        else:
            new_product = Product(name=form.name.data, description=form.description.data, price=form.price.data)
            db.session.add(new_product)
            flash('Product added successfully')
        db.session.commit()
        return redirect(url_for('admin_panel'))

    products = Product.query.all()
    return render_template('admin_panel.html', form=form, products=products)

@app.route('/admin/edit/<int:product_id>')
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.id.data = product.id
    return render_template('admin_panel.html', form=form, products=Product.query.all())

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    print("Received CSRF token:", request.form.get('csrf_token'))  # Check the received CSRF token
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully')
    return redirect(url_for('admin_panel'))

# Main entry
if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create a default admin user if it doesn't exist
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", password="admin", is_admin=True)
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)
