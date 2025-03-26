import sqlite3
from flask import Flask, render_template, request, redirect, url_for

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
                 price REAL,
                 quantity INTEGER
                 )''')
    conn.commit()
    conn.close()

def verify_admin(username):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        return True
    return False

@app.route('/admin/products')
def admin_products():
    if not verify_admin(request.cookies.get('username')):
        return redirect(url_for('login'))  # Replace with your login route
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('admin_products.html', products=products)

# ... routes for adding, editing, and deleting products

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)