from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random value

# Initialize database
conn = sqlite3.connect('products.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL
    )
''')
conn.commit()
conn.close()

# Mock admin user (in real application, fetch from database)
admin_user = {'username': 'admin', 'password': 'adminpassword'}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_user['username'] and password == admin_user['password']:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Fetch products from the database
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', products=products)

@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_product.html')

@app.route('/admin/remove_product/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    # Check if the product exists
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return "Product does not exist", 404
    
    # Remove the product
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/modify_product/<int:product_id>', methods=['GET', 'POST'])
def modify_product(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    # Fetch the product to modify
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return "Product does not exist", 404
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        cursor.execute('UPDATE products SET name=?, description=?, price=? WHERE id=?',
                       (name, description, price, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    conn.close()
    return render_template('modify_product.html', product=product)

if __name__ == '__main__':
    app.run(debug=True)