from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired
from flask import session

db = SQLAlchemy()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Adjust for your database
db.init_app(app)

@app.before_request
def set_admin_session():
    session['is_admin'] = False

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    # Description column might not exist in your table
    description = db.Column(db.Text, nullable=True)  # Adjust data type if needed
    price = db.Column(db.Float)

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Submit')

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/admin/products')
def admin_products():
    if not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))
    products = Product.query.all()
    return render_template('admin_products.html', products=products, form=ProductForm())


@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():
    if not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        product = Product(name=name, description=description, price=price)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin_products'))

    return render_template('add_product.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Replace with your actual authentication logic   

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            session['is_admin'] = user.is_admin  # Set admin status in session
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_products'))  # Redirect to admin products page
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/admin/products/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    if not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get(product_id)

    if product:
        if request.method == 'POST':
            db.session.delete(product)
            db.session.commit()
            flash('Product deleted successfully.', 'success')
            return redirect(url_for('admin_products'))

        return render_template('delete_product.html', product=product)
    else:
        flash('Product not found.', 'warning')
        return redirect(url_for('admin_products'))

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('is_admin'):
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('login'))

    product = Product.query.get(product_id)

    if product:
        form = ProductForm(obj=product)

        if request.method == 'POST':
            if form.validate_on_submit():
                product.name = form.name.data
                product.description = form.description.data
                product.price = form.price.data
                db.session.commit()
                flash('Product updated successfully.', 'success')
                return redirect(url_for('admin_products'))

        return render_template('edit_product.html', product=product, form=form)
    else:
        flash('Product not found.', 'warning')
        return redirect(url_for('admin_products'))

if __name__ == '__main__':
    app.run(debug=True)