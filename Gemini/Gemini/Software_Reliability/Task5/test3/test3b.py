import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def connect_db():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL
    )''')
    conn.commit()
    return conn

def get_db():
    if not hasattr(app, 'db'):
        app.db = connect_db()
    return app.db

def is_admin(user_id):
    # Replace with your actual user authentication logic
    # Here's a simplified example using a static admin ID
    return user_id == 1  # Change 1 to your actual admin user ID

@app.route('/admin/products')
def admin_products():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    if is_admin(request.cookies.get('user_id')):
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        quantity = request.form['quantity']
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO products (name, description, price, quantity) VALUES (?, ?, ?, ?)", (name, description, price, quantity))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))
    else:
        return "You don't have admin privileges."

# Implement similar routes for editing and deleting products

if __name__ == '__main__':
    app.run(debug=True)