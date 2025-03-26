import sqlite3
from flask import Flask, request, render_template, redirect, url_for

def create_tables():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                is_admin BOOLEAN
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                price REAL
            )''')

    conn.commit()
    conn.close()

app = Flask(__name__)

# Assuming you have a function to get the current user's username and admin status
def get_current_user_info():
    # ... your logic here ...
    return username, is_admin

# ... other routes and functions ...

@app.route('/products')
def products():
    username, is_admin = get_current_user_info()
    if not is_admin:
        return "You don't have admin privileges."

    # Fetch products from the database
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    products = c.execute('SELECT * FROM products').fetchall()
    conn.close()

    return render_template('products.html', products=products)

# ... routes for adding, editing, and deleting products ...