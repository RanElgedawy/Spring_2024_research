from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_wtf import CSRFProtect
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with your secret key
csrf = CSRFProtect(app)

DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    with get_db() as conn:
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute("DROP TABLE IF EXISTS products")
        
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            username TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL,
                            is_admin INTEGER NOT NULL DEFAULT 0)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            description TEXT NOT NULL,
                            price REAL NOT NULL)''')

def init_admin_user():
    with get_db() as conn:
        conn.execute('''INSERT OR IGNORE INTO users (username, password, is_admin) 
                        VALUES ('admin', 'adminpassword', 1)''')

create_tables()
init_admin_user()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                                (username, password)).fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials')
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/admin/products', methods=['GET'])
@admin_required
def admin_products():
    with get_db() as conn:
        products = conn.execute('SELECT * FROM products').fetchall()
    return render_template('admin_products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        
        with get_db() as conn:
            conn.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                         (name, description, price))
            conn.commit()
        
        flash('Product added successfully')
        return redirect(url_for('admin_products'))
    
    return render_template('add_product.html')

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    with get_db() as conn:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        
        if not product:
            flash('Product does not exist.')
            return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        
        with get_db() as conn:
            conn.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                         (name, description, price, product_id))
            conn.commit()
        
        flash('Product updated successfully')
        return redirect(url_for('admin_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    with get_db() as conn:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        
        if not product:
            flash('Product does not exist.')
            return redirect(url_for('admin_products'))
        
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
    
    flash('Product deleted successfully')
    return redirect(url_for('admin_products'))

if __name__ == '__main__':
    app.run(debug=True)