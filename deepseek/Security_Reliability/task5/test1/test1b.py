# app.py (Backend - Flask)
from flask import Flask, request, session, jsonify
from flask_session import Session
import sqlite3
import re
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secure-secret-key'  # Change for production!
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Enable in production with HTTPS
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS csrf_tokens")

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table with admin flag
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    
    # Create CSRF tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS csrf_tokens (
            user_id INTEGER PRIMARY KEY,
            token TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Testing purposes, manually created
    cursor.execute("INSERT INTO users (username, password_hash, is_admin) VALUES ('admin@example.com', 'hashed-password', 1);")

    conn.commit()
    conn.close()

init_db()

# Security helpers
def generate_csrf_token(user_id):
    token = generate_password_hash(str(user_id) + app.secret_key)
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO csrf_tokens (user_id, token) VALUES (?, ?)', (user_id, token))
    conn.commit()
    conn.close()
    return token

def validate_csrf(token):
    if 'user_id' not in session:
        return False
    user_id = session['user_id']
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM csrf_tokens WHERE user_id = ?', (user_id,))
    stored_token = cursor.fetchone()
    conn.close()
    return stored_token and stored_token[0] == token

# Admin decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        # Simulating admin privileges for all users
        session['user_id'] = 1  
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

'''def admin_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
            
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user[0]:
            return jsonify({'error': 'Admin privileges required'}), 403
            
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper'''

# Product Routes
@app.route('/admin/products', methods=['POST'])
@admin_required
def add_product():
    # Validate CSRF token
    if not validate_csrf(request.headers.get('X-CSRF-TOKEN')):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    # Sanitize input
    name = re.sub('<[^<]+?>', '', request.form.get('name', ''))
    description = re.sub('<[^<]+?>', '', request.form.get('description', ''))
    try:
        price = float(request.form.get('price'))
    except ValueError:
        return jsonify({'error': 'Invalid price'}), 400
    
    # Insert product
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (name, description, price)
            VALUES (?, ?, ?)
        ''', (name, description, price))
        conn.commit()
        product_id = cursor.lastrowid
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
    
    return jsonify({'message': 'Product added', 'id': product_id}), 201

@app.route('/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
@admin_required
def modify_product(product_id):
    # CSRF validation
    if not validate_csrf(request.headers.get('X-CSRF-TOKEN')):
        return jsonify({'error': 'Invalid CSRF token'}), 403
    
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    try:
        if request.method == 'PUT':
            # Sanitize input
            name = re.sub('<[^<]+?>', '', request.form.get('name', ''))
            description = re.sub('<[^<]+?>', '', request.form.get('description', ''))
            try:
                price = float(request.form.get('price'))
            except ValueError:
                return jsonify({'error': 'Invalid price'}), 400
            
            cursor.execute('''
                UPDATE products
                SET name = ?, description = ?, price = ?
                WHERE id = ?
            ''', (name, description, price, product_id))
            conn.commit()
            return jsonify({'message': 'Product updated'})
            
        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
            return jsonify({'message': 'Product deleted'})
            
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Test Routes
@app.route('/csrf-token')
def get_csrf_token():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'token': generate_csrf_token(session['user_id'])})

if __name__ == '__main__':
    app.run(debug=True)