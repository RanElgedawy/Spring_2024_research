import sqlite3
import flask
from flask import session

app = flask.Flask(__name__)
app.secret_key = 'your_secret_key'

def connect_db():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = connect_db()
    with db:
        db.executescript('''
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS products;
                         
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            );
        ''')

def check_admin(username):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result and result['is_admin']

def validate_user(username, password):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user and user['password'] == password: 
  # Compare hashed passwords in production
        return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        password = flask.request.form['password'] 


        if validate_user(username, password):
            session['username'] = username  # Store username in session
            return flask.redirect('/admin/products')  # Redirect to admin panel
        else:
            error = 'Invalid username or password'  # Handle login failure
            return flask.render_template('login.html', error=error)

    return flask.render_template('login.html')

@app.route('/admin/products')
def admin_products():
    if not check_admin(flask.session['username']):
        return flask.redirect('/')  # Redirect to login or unauthorized page

    db = connect_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return flask.render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if not check_admin(flask.session['username']):
        return flask.redirect('/')  # Redirect to login or unauthorized page

    if flask.request.method == 'POST':
        name = flask.request.form['name']
        description = flask.request.form['description']
        price = flask.request.form['price']

        # Validate input (e.g., check for empty fields, valid price format)

        db = connect_db()
        db.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                  (name, description, price))
        db.commit()
        return flask.redirect('/admin/products')  # Redirect to product list

    return flask.render_template('admin_add_product.html')

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if not check_admin(flask.session['username']):
        return flask.redirect('/')  # Redirect to login or unauthorized page

    db = connect_db()
    cursor = db.cursor()
    cursor.execute('SELECT 1 FROM products WHERE id = ?', (product_id,))
    result = cursor.fetchone()

    if result:
        db.execute('DELETE FROM products WHERE id = ?', (product_id,))
        db.commit()
        return flask.redirect('/admin/products')  # Redirect to product list
    else:
        # Handle product not found (e.g., show an error message)
        return flask.render_template('product_not_found.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not check_admin(flask.session['username']):
        return flask.redirect('/')  # Redirect to login or unauthorized page

    db = connect_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product:
        return flask.render_template('product_not_found.html')

    if flask.request.method == 'POST':
        name = flask.request.form['name']
        description = flask.request.form['description']
        price = flask.request.form['price']

        # Validate input (e.g., check for empty fields, valid price format)

        db.execute('UPDATE products SET name = ?, description = ?, price = ? WHERE id = ?',
                  (name, description, price, product_id))
        db.commit()
        return flask.redirect('/admin/products')  # Redirect to product list

    return flask.render_template('admin_edit_product.html', product=product)

def insert_test_user(username, password, is_admin=False):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                  (username, password, is_admin))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    insert_test_user("admin", "password123")
    app.run(debug=True)