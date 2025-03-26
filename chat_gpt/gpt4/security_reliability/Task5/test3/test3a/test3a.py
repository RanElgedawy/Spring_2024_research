from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_wtf.csrf import CSRFProtect
import sqlite3
import os
import html

app = Flask(__name__)
app.secret_key = 'your_secret_key'
csrf = CSRFProtect(app)

# Path to your SQLite database
DATABASE = 'ecommerce.db'

# Function to get database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Close the database when the app context ends
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create necessary tables for users and products (run once)
def create_tables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
                       
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            )
        ''')

        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (1, 'test', 'test', 1))
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        db.commit()

# Simple authentication and admin checking (replace with real auth in production)
def is_admin():
    return session.get('is_admin', False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user[0]
            session['is_admin'] = user[3]  # Assuming the 4th field is is_admin
            flash('Login successful!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@csrf.exempt  # CSRF protection for forms
def admin_panel():
    if not is_admin():
        flash('Admin privileges required!', 'danger')
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        product_id = request.form.get('product_id', None)
        name = html.escape(request.form.get('name', ''))
        description = html.escape(request.form.get('description', ''))
        price = request.form.get('price')

        try:
            price = float(price)
        except ValueError:
            flash('Invalid price format!', 'danger')
            return redirect(url_for('admin_panel'))

        if action == 'add':
            db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
            flash('Product added successfully!', 'success')
        elif action == 'edit' and product_id:
            db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?', (name, description, price, product_id))
            flash('Product updated successfully!', 'success')
        elif action == 'delete' and product_id:
            db.execute('DELETE FROM products WHERE id = ?', (product_id,))
            flash('Product deleted successfully!', 'success')
        
        db.commit()

    # Fetch all products for display
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('admin_panel.html', products=products)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_tables()  # Ensure tables are created
    app.run(debug=True)