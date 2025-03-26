from flask import Flask, render_template_string, request, redirect, url_for, session, abort, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'  # Change this in production!
csrf = CSRFProtect(app)

DATABASE = 'app.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Insert test users if they don’t already exist
    try:
        cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("admin", 1))
    except sqlite3.IntegrityError:
        pass
    try:
        cursor.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("user", 0))
    except sqlite3.IntegrityError:
        pass
    # Insert a sample product if none exists
    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()['count'] == 0:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                       ("Test Product", "This is a test product.", 9.99))
    conn.commit()
    conn.close()

init_db()

# Decorator to check admin privileges
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Admin privileges required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# WTForms class for product add/edit
class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

# Simple login route for testing (assumes no password for simplicity)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user:
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            flash(f"Logged in as {user['username']}", "success")
            return redirect(url_for('admin_products'))
        else:
            flash("User not found.", "danger")
    return render_template_string('''
    <!doctype html>
    <title>Login</title>
    <h1>Login</h1>
    <form method="post">
      <label>Username:</label>
      <input type="text" name="username">
      <input type="submit" value="Login">
    </form>
    <p>Test with username <strong>admin</strong> (has admin rights) or <strong>user</strong> (regular user).</p>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for('login'))

# List products (admin only)
@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template_string('''
    <!doctype html>
    <title>Products</title>
    <h1>Products</h1>
    <a href="{{ url_for('add_product') }}">Add Product</a>
    <ul>
    {% for product in products %}
      <li>
         <strong>{{ product['name'] }}</strong> - {{ product['description'] }} - ${{ product['price'] }}
         <a href="{{ url_for('edit_product', product_id=product['id']) }}">Edit</a>
         <form action="{{ url_for('delete_product', product_id=product['id']) }}" method="post" style="display:inline;">
           <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
           <input type="submit" value="Delete" onclick="return confirm('Are you sure?');">
         </form>
      </li>
    {% endfor %}
    </ul>
    <a href="{{ url_for('logout') }}">Logout</a>
    ''', products=products)

# Add a product (admin only)
@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        conn.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                     (form.name.data, form.description.data, float(form.price.data)))
        conn.commit()
        conn.close()
        flash("Product added successfully.", "success")
        return redirect(url_for('admin_products'))
    return render_template_string('''
    <!doctype html>
    <title>Add Product</title>
    <h1>Add Product</h1>
    <form method="post">
      {{ form.hidden_tag() }}
      <p>
        {{ form.name.label }}<br>
        {{ form.name(size=32) }}
      </p>
      <p>
        {{ form.description.label }}<br>
        {{ form.description(rows=4, cols=40) }}
      </p>
      <p>
        {{ form.price.label }}<br>
        {{ form.price() }}
      </p>
      <p>{{ form.submit() }}</p>
    </form>
    <a href="{{ url_for('admin_products') }}">Back to Products</a>
    ''', form=form)

# Edit a product (admin only)
@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        abort(404)
    # Pre-populate form with current product data
    form = ProductForm(data=product)
    if form.validate_on_submit():
        conn.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                     (form.name.data, form.description.data, float(form.price.data), product_id))
        conn.commit()
        conn.close()
        flash("Product updated successfully.", "success")
        return redirect(url_for('admin_products'))
    conn.close()
    return render_template_string('''
    <!doctype html>
    <title>Edit Product</title>
    <h1>Edit Product</h1>
    <form method="post">
      {{ form.hidden_tag() }}
      <p>
        {{ form.name.label }}<br>
        {{ form.name(size=32) }}
      </p>
      <p>
        {{ form.description.label }}<br>
        {{ form.description(rows=4, cols=40) }}
      </p>
      <p>
        {{ form.price.label }}<br>
        {{ form.price() }}
      </p>
      <p>{{ form.submit() }}</p>
    </form>
    <a href="{{ url_for('admin_products') }}">Back to Products</a>
    ''', form=form)

# Delete a product (admin only)
@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted successfully.", "success")
    return redirect(url_for('admin_products'))

if __name__ == '__main__':
    app.run(debug=True)
