from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField, PasswordField, HiddenField
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong, random secret key

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)

class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('Product Name')
    description = TextAreaField('Description')
    price = FloatField('Price')
    submit = SubmitField('Submit')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin_products'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if not current_user.is_admin:
        return "You are not authorized to access this page."

    form = ProductForm()
    if form.validate_on_submit():
        # Create or update product
        if form.id.data:
            product = Product.query.get(form.id.data)
            if product:
                product.name = form.name.data
                product.description = form.description.data
                product.price = form.price.data
                db.session.commit()
                flash('Product updated successfully')
            else:
                flash('Product not found')
        else:
            product = Product(name=form.name.data, description=form.description.data, price=form.price.data)
            db.session.add(product)
            db.session.commit()
            flash('Product created successfully')
        return redirect(url_for('admin_products'))

    products = Product.query.all()
    return render_template('admin_products.html', form=form, products=products)

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        return "You are not authorized to access this page."

    product = Product.query.get(product_id)
    if product:
        form = ProductForm(obj=product)
        if form.validate_on_submit():
            # Update product
            product.name = form.name.data
            product.description = form.description.data
            product.price = form.price.data
            db.session.commit()
            flash('Product updated successfully')
            return redirect(url_for('admin_products'))
        return render_template('admin_products.html', form=form, products=[])
    else:
        flash('Product not found')
        return redirect(url_for('admin_products'))

@app.route('/admin/products/<int:product_id>/delete')
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return "You are not authorized to access this page."

    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully')
    else:
        flash('Product not found')
    return redirect(url_for('admin_products'))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Add a sample admin user
        admin_user = User(username='admin', password_hash=generate_password_hash('password'))
        admin_user.is_admin = True
        db.session.add(admin_user)
        db.session.commit()
    app.run(debug=True)