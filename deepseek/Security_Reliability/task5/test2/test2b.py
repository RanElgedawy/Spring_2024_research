from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required
from flask_wtf.csrf import CSRFProtect
import sqlite3
from werkzeug.security import generate_password_hash
import os
import html

app = Flask(__name__)
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

DATABASE = 'ecommerce.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        admin_exists = cursor.execute('SELECT 1 FROM users WHERE username="admin"').fetchone()
        if not admin_exists:
            cursor.execute(
                'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)',
                ('admin', generate_password_hash('admin'))
        conn.commit()

init_db()

class User(UserMixin):
    def __init__(self, id, is_admin):
        self.id = id
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        user = cursor.execute(
            'SELECT id, is_admin FROM users WHERE id = ?', (user_id,)
        ).fetchone()
    return User(*user) if user else None

def admin_required(f):
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            user = cursor.execute(
                'SELECT id, password_hash FROM users WHERE username = ?',
                (request.form['username'],)
            ).fetchone()
        if user and check_password_hash(user[1], request.form['password']):
            login_user(User(user[0], True))
            return redirect(url_for('manage_products'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/admin/products')
@login_required
@admin_required
def manage_products():
    with sqlite3.connect(DATABASE) as conn:
        products = conn.execute(
            'SELECT id, name, price FROM products'
        ).fetchall()
    return render_template('manage_products.html', products=products)

@app.route('/admin/products/add', methods=['POST'])
@login_required
@admin_required
def add_product():
    name = html.escape(request.form['name'])
    description = html.escape(request.form['description'])
    price = float(request.form['price'])
    
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            'INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
            (name, description, price)
        )
    flash('Product added', 'success')
    return redirect(url_for('manage_products'))

@app.route('/admin/products/update/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_product(id):
    name = html.escape(request.form['name'])
    description = html.escape(request.form['description'])
    price = float(request.form['price'])
    
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            'UPDATE products SET name=?, description=?, price=? WHERE id=?',
            (name, description, price, id)
        )
    flash('Product updated', 'success')
    return redirect(url_for('manage_products'))

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('DELETE FROM products WHERE id = ?', (id,))
    flash('Product deleted', 'success')
    return redirect(url_for('manage_products'))

if __name__ == '__main__':
    app.run(debug=True)