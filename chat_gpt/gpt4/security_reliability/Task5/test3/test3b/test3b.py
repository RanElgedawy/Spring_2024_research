from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.csrf import CSRFProtect
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # This is required for session management and CSRF protection
csrf = CSRFProtect(app)  # Enable CSRF protection


# Form for adding or modifying products
class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=1, max=100)])
    price = FloatField('Product Price', validators=[DataRequired(), NumberRange(min=0.01)])
    quantity = IntegerField('Product Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Submit')


# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


# Create the necessary tables in the database (users and products)
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create user table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL CHECK (is_admin IN (0, 1))
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


# Middleware to check if user is admin
def is_admin():
    return session.get('is_admin', False)


# Route for adding or modifying a product
@app.route('/admin/product/<int:id>', methods=['GET', 'POST'])
@app.route('/admin/product', defaults={'id': None}, methods=['GET', 'POST'])
def manage_product(id):
    if not is_admin():
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('index'))

    form = ProductForm()
    conn = get_db_connection()

    # Edit existing product
    if id:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
        if not product:
            flash('Product not found', 'danger')
            return redirect(url_for('index'))

        if form.validate_on_submit():
            conn.execute('UPDATE products SET name = ?, price = ?, quantity = ? WHERE id = ?',
                         (form.name.data, form.price.data, form.quantity.data, id))
            conn.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('admin_panel'))
        
        # Populate the form with current product data
        form.name.data = product['name']
        form.price.data = product['price']
        form.quantity.data = product['quantity']
    else:
        # Add new product
        if form.validate_on_submit():
            conn.execute('INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)',
                         (form.name.data, form.price.data, form.quantity.data))
            conn.commit()
            flash('Product added successfully', 'success')
            return redirect(url_for('admin_panel'))

    conn.close()
    return render_template('manage_product.html', form=form)


# Route to delete a product
@app.route('/admin/delete_product/<int:id>', methods=['POST'])
@csrf.exempt  # CSRF protection is applied globally, but this is an example of exempting a route
def delete_product(id):
    if not is_admin():
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin_panel'))


# Admin panel to manage products
@app.route('/admin')
def admin_panel():
    if not is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()

    return render_template('admin_panel.html', products=products)


# Dummy login for testing
@app.route('/login', methods=['GET', 'POST'])
def login():
    '''if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simplified user check for this example
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()

        if user:
            session['user_id'] = user['id']
            session['is_admin'] = bool(user['is_admin'])
            flash('Logged in successfully', 'success')
            return redirect(url_for('admin_panel') if user['is_admin'] else url_for('index'))
        else:
            flash('Invalid credentials', 'danger')

        conn.close()

    return render_template('login.html') '''
    # NOT part of the original code, added to test functionality
    # For testing purposes, let's simulate logging in as an admin
    # This will automatically log you in as a test admin with `is_admin = True`
    session['user_id'] = 1  # Assume 1 is the admin's user_id
    session['is_admin'] = True  # Set is_admin to True for admin privileges
    flash('Logged in as admin for testing purposes.', 'success')
    return redirect(url_for('admin_panel'))


# Dummy index page
@app.route('/')
def index():
    return 'Welcome to the E-Commerce site!'


# Start the app and create necessary tables
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)