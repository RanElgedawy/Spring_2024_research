from flask import Flask, render_template_string, request, redirect, url_for, session, flash, g
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange
import sqlite3
import os

# Configuration
DATABASE = 'ecommerce.db'
SECRET_KEY = 'replace-with-a-secure-random-key'

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# --- Database Helpers ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Create tables for users and products
    db.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
                     
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            is_admin INTEGER NOT NULL DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
    """)
    # Insert an admin user for testing (if not exists)
    cur = db.execute("SELECT id FROM users WHERE username = ?", ('admin',))
    if cur.fetchone() is None:
        db.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('admin', 0))
        db.commit()

# --- Forms using Flask-WTF (includes CSRF protection) ---
class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Description', validators=[Length(max=500)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')
    # A hidden field to store product ID when editing
    product_id = HiddenField('Product ID')

# --- Helper to check admin status ---
def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash("Please log in as admin to access this page.", "error")
            return redirect(url_for('login_admin'))
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or not user['is_admin']:
            flash("You do not have the required privileges.", "error")
            return redirect(url_for('login_admin'))
        return func(*args, **kwargs)
    return wrapper

# --- Routes ---

# Test login to simulate admin login (for testing only)
@app.route('/login_admin')
def login_admin():
    db = get_db()
    admin = db.execute("SELECT * FROM users WHERE username = ?", ('admin',)).fetchone()
    if admin:
        session['user_id'] = admin['id']
        flash("Logged in as admin.", "success")
    return redirect(url_for('list_products'))

# List products (admin view)
@app.route('/admin/products')
@admin_required
def list_products():
    db = get_db()
    products = db.execute("SELECT * FROM products").fetchall()
    return render_template_string("""
        <h1>Products</h1>
        <a href="{{ url_for('add_product') }}">Add New Product</a>
        <ul>
        {% for p in products %}
            <li>
                <strong>{{ p['name'] }}</strong> - ${{ p['price'] }}<br>
                {{ p['description']|e }}<br>
                <a href="{{ url_for('edit_product', product_id=p['id']) }}">Edit</a> |
                <form action="{{ url_for('delete_product', product_id=p['id']) }}" method="post" style="display:inline;">
                    {{ csrf_field() }}
                    <button type="submit" onclick="return confirm('Are you sure?');">Delete</button>
                </form>
            </li>
        {% endfor %}
        </ul>
    """, products=products)

# Add a new product
@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        db = get_db()
        db.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
                   (form.name.data, form.description.data, float(form.price.data)))
        db.commit()
        flash("Product added successfully.", "success")
        return redirect(url_for('list_products'))
    return render_template_string("""
        <h1>Add Product</h1>
        <form method="post">
            {{ form.hidden_tag() }}
            <p>
                {{ form.name.label }}<br>
                {{ form.name(size=50) }}
            </p>
            <p>
                {{ form.description.label }}<br>
                {{ form.description(size=100) }}
            </p>
            <p>
                {{ form.price.label }}<br>
                {{ form.price() }}
            </p>
            <p>{{ form.submit() }}</p>
        </form>
        <a href="{{ url_for('list_products') }}">Back to Products</a>
    """, form=form)

# Edit an existing product
@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for('list_products'))
    form = ProductForm(data=product)
    # Set hidden field to track product id
    form.product_id.data = product_id
    if form.validate_on_submit():
        db.execute("UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?",
                   (form.name.data, form.description.data, float(form.price.data), product_id))
        db.commit()
        flash("Product updated successfully.", "success")
        return redirect(url_for('list_products'))
    return render_template_string("""
        <h1>Edit Product</h1>
        <form method="post">
            {{ form.hidden_tag() }}
            <p>
                {{ form.name.label }}<br>
                {{ form.name(size=50) }}
            </p>
            <p>
                {{ form.description.label }}<br>
                {{ form.description(size=100) }}
            </p>
            <p>
                {{ form.price.label }}<br>
                {{ form.price() }}
            </p>
            <p>{{ form.submit() }}</p>
        </form>
        <a href="{{ url_for('list_products') }}">Back to Products</a>
    """, form=form)

# Delete a product (POST only)
@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash("Product deleted successfully.", "success")
    return redirect(url_for('list_products'))

# A helper to insert CSRF token in manual forms (for delete form)
@app.context_processor
def csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_field=lambda: '<input type="hidden" name="csrf_token" value="{}">'.format(generate_csrf()))

# Main entry point
if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    app.run(debug=True)
