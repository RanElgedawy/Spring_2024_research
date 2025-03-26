from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Random secret key for session management

# Database initialization and connection
conn = sqlite3.connect('products.db', check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute('''CREATE TABLE IF NOT EXISTS products
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL)''')
conn.commit()

# Example admin user (in practice, use a more secure authentication mechanism)
admin_user = {'username': 'admin', 'password': hashlib.sha256(b'admin_password').hexdigest()}


# Function to check admin privileges
def is_admin():
    return session.get('username') == admin_user['username']


# Routes for adding, modifying, and removing products
@app.route('/')
def index():
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return render_template('index.html', products=products, is_admin=is_admin())


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST' and is_admin():
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
        conn.commit()
        return redirect(url_for('index'))
    return render_template('add_product.html', is_admin=is_admin())


@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if is_admin():
        cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
        product = cursor.fetchone()
        if not product:
            return redirect(url_for('index'))  # Redirect if product doesn't exist
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            cursor.execute('UPDATE products SET name=?, description=?, price=? WHERE id=?',
                           (name, description, price, product_id))
            conn.commit()
            return redirect(url_for('index'))
        else:
            return render_template('edit_product.html', product=product, is_admin=is_admin())
    else:
        return redirect(url_for('index'))


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if is_admin():
        cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
        product = cursor.fetchone()
        if product:
            cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
            conn.commit()
    return redirect(url_for('index'))


# Login route (simplified for demonstration purposes, implement a more secure login mechanism)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        if username == admin_user['username'] and password == admin_user['password']:
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)