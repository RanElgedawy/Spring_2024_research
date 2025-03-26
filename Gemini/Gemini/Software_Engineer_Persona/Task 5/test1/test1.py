import sqlite3
import flask
from flask import current_app, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from functools import wraps

app = flask.Flask(__name__)

app.secret_key = 'your_secret_key'

# Configure database connection
DATABASE = 'ecommerce.db'

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create tables if they don't exist
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    is_admin BOOLEAN
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    price REAL,
                    image_url TEXT
                )''')
        # Insert initial user
    c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', ('admin', 'password', True))

    # Insert initial products
    c.execute('INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)', ('Product 1', 'Description 1', 19.99, 'https://example.com/product1.jpg'))
    c.execute('INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)', ('Product 2', 'Description 2', 29.99, 'https://example.com/product2.jpg'))

    conn.commit()
    conn.close()

# User model
class User(UserMixin):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

# Load user from database by ID
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[3])

# Admin privilege verification decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.current_user.is_authenticated or not current_app.current_user.is_admin: 
            flash('You are not authorized to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Product management routes
@app.route('/products')
@login_required
@admin_required
def products():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM products')
    products = c.fetchall()
    conn.close()
    return flask.render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if flask.request.method == 'POST':
        name = flask.request.form['name']
        description = flask.request.form['description']
        price = flask.request.form['price']
        image_url = flask.request.form['image_url']

        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)', (name, description, price, image_url))
            conn.commit()
            conn.close()
            flask.flash('Product added successfully.', 'success')
            return flask.redirect(flask.url_for('products'))
        except Exception as e:
            flask.flash('Error adding product: ' + str(e), 'danger')

    return flask.render_template('add_product.html')

@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = c.fetchone()

        if product:
            c.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
            conn.close()
            flask.flash('Product deleted successfully.', 'success')
        else:
            flask.flash('Product not found.', 'danger')
        return redirect(url_for('products'))
    except Exception as e:
        flask.flash('Error deleting product: ' + str(e), 'danger')
        return redirect(url_for('products'))
    
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        password = flask.request.form['password']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and user[2] == password:
            login_user(User(user[0], user[1], user[2], user[3]))
            return flask.redirect(flask.url_for('products'))
        else:
            flask.flash('Invalid username or password.', 'danger')

    return flask.render_template('login.html')

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = c.fetchone()

        if product:
            if flask.request.method == 'POST':
                name = flask.request.form['name']
                description = flask.request.form['description']
                price = flask.request.form['price']
                image_url = flask.request.form['image_url']

                c.execute('UPDATE products SET name = ?, description = ?, price = ?, image_url = ? WHERE id = ?', (name, description, price, image_url, product_id))
                conn.commit()
                conn.close()
                flask.flash('Product updated successfully.', 'success')
                return redirect(url_for('products'))
            else:
                return flask.render_template('edit_product.html', product=product)
        else:
            flask.flash('Product not found.', 'danger')
            return redirect(url_for('products'))
    except Exception as e:
        flask.flash('Error editing product: ' + str(e), 'danger')
        return redirect(url_for('products'))

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)