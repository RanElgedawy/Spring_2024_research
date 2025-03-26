from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # In production, use a proper secret key

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        # Insert test admin user if none exists
        admin = cursor.execute('SELECT * FROM users WHERE is_admin = 1').fetchone()
        if not admin:
            cursor.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)',
                         ('admin', 1))
        
        conn.commit()
        conn.close()

init_db()

# Security middleware
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            abort(403)
            
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if not user or not user['is_admin']:
            abort(403)
            
        return f(*args, **kwargs)
    return decorated

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = os.urandom(16).hex()
    return session['csrf_token']

def validate_csrf():
    token = request.form.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        abort(403)

# Context processor with callable function
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf_token)  # Pass the function itself, not its result

# Routes
@app.route('/simulate-login/<username>')
def simulate_login(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        return f'Logged in as {username} (Admin)' if user['is_admin'] else f'Logged in as {username}'
    return 'User not found'

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', products=products)

# Then modify the add_product route to remove explicit csrf_token passing
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        validate_csrf()
        name = request.form['name'].strip()
        description = request.form['description'].strip()
        price = float(request.form['price'])
        
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                   (name, description, price))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_product.html')  # No need to pass csrf_token explicitly

# Edit product route
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if not product:
        conn.close()
        abort(404)
    
    if request.method == 'POST':
        validate_csrf()
        name = request.form['name'].strip()
        description = request.form['description'].strip()
        price = float(request.form['price'])
        
        conn.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                   (name, description, price, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    validate_csrf()
    conn = get_db_connection()
    
    # First check if product exists
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if not product:
        conn.close()
        abort(404)  # Not found
    
    # If product exists, proceed with deletion
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)