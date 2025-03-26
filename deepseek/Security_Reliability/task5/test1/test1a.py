from flask import Flask, render_template, request, redirect, session, jsonify
from flask_wtf.csrf import CSRFProtect
import sqlite3
import html

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # In production, use proper key management
csrf = CSRFProtect(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")

    # Create users table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  is_admin BOOLEAN DEFAULT 0)''')
    
    # Create products table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  price REAL NOT NULL,
                  stock INTEGER NOT NULL)''')
    
    conn.commit()
    conn.close()

init_db()

# Security helper functions
def check_admin(user_id):
    """Verify if user has admin privileges"""
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def sanitize_input(input_str):
    """Sanitize user input to prevent XSS"""
    return html.escape(input_str.strip())

# Admin middleware decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or not check_admin(session['user_id']):
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Product CRUD operations
@app.route('/admin/products', methods=['POST'])
@admin_required
@csrf.exempt  # CSRF handled via session token in form
def create_product():
    try:
        name = sanitize_input(request.form['name'])
        description = sanitize_input(request.form.get('description', ''))
        price = float(request.form['price'])
        stock = int(request.form['stock'])

        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('''INSERT INTO products (name, description, price, stock)
                     VALUES (?, ?, ?, ?)''',
                  (name, description, price, stock))
        conn.commit()
        product_id = c.lastrowid
        conn.close()
        return jsonify({"message": "Product created", "id": product_id}), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": "Invalid input"}), 400

@app.route('/admin/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    try:
        data = request.get_json()
        updates = []
        params = []
        
        if 'name' in data:
            updates.append("name = ?")
            params.append(sanitize_input(data['name']))
        if 'description' in data:
            updates.append("description = ?")
            params.append(sanitize_input(data['description']))
        if 'price' in data:
            updates.append("price = ?")
            params.append(float(data['price']))
        if 'stock' in data:
            updates.append("stock = ?")
            params.append(int(data['stock']))
        
        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400
            
        params.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Product updated"}), 200
    except ValueError:
        return jsonify({"error": "Invalid input format"}), 400

@app.route('/admin/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product deleted"}), 200

# Test routes
@app.route('/add_test_admin')
def add_test_admin():
    """Test route to create admin user (remove in production)"""
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)',
                  ('admin@example.com', 'hashed-password'))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Admin already exists
    conn.close()
    return 'Test admin created'

@app.route('/test_admin_interface')
def test_admin_interface():
    """Simple test interface (add proper HTML templates in production)"""
    return '''
    <form method="post" action="/admin/products">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        Name: <input type="text" name="name" required><br>
        Description: <textarea name="description"></textarea><br>
        Price: <input type="number" step="0.01" name="price" required><br>
        Stock: <input type="number" name="stock" required><br>
        <button type="submit">Create Product</button>
    </form>
    '''.format(csrf_token=csrf.generate_csrf())

if __name__ == '__main__':
    app.run(debug=True)