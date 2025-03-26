import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response

app = Flask(__name__)

def connect_db():
    conn = sqlite3.connect('ecommerce.db')
    return conn

def create_tables():
    conn = connect_db()
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
                )''')
    c.execute("INSERT INTO users (username, password, is_admin) VALUES ('admin', 'password123', 1)")
    conn.commit()
    conn.close()

def check_admin(username):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db() 

        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user: 

            # Set a cookie to indicate successful login
            response = make_response(redirect(url_for('admin_products')))
            response.set_cookie('username', username)
            return response
        else:
            return "Invalid username or password"
    return render_template('login.html')

def convert_to_dict(tuple_data):
    return dict(zip(['id', 'name', 'description', 'price', 'quantity'], tuple_data))

@app.route('/admin/products')
def admin_products():
    if not check_admin(request.cookies.get('username')):
        return redirect(url_for('login'))  # Assuming a login route exists
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    products = [convert_to_dict(product) for product in products]
    conn.close()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_products_add():
    if not check_admin(request.cookies.get('username')):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        quantity = request.form['quantity'] 

        conn = connect_db()
        c = conn.cursor()
        c.execute("INSERT INTO products (name, description, price, quantity) VALUES (?, ?, ?, ?)", (name, description, price, quantity))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))
    return render_template('admin_products_add.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_products_edit(product_id):
    if not check_admin(request.cookies.get('username')):
        return redirect(url_for('login'))
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = c.fetchone()
    conn.close()
    if not product:
        return "Product not found."
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        quantity = request.form['quantity'] 

        conn = connect_db()
        c = conn.cursor()
        c.execute("UPDATE products SET name=?, description=?, price=?, quantity=? WHERE id=?", (name, description, price, quantity, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))
    return render_template('admin_products_edit.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
def admin_products_delete(product_id):
    if not check_admin(request.cookies.get('username')):
        return redirect(url_for('login'))
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = c.fetchone()
    if product:
        c.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))
    else:
        conn.close()
        return "Product not found."

if __name__ == '__main__':
    create_tables()
    app.run()