from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Function to create the database and tables if they don't exist
def create_tables():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    # To prevent conflict with potentially already existing databases
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    admin INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    price REAL,
                    description TEXT
                )''')
    # Manually added for testing purposes 
    c.execute("INSERT INTO users (username, password, admin) VALUES (?,?,?)", ("admin", "adminpass", 1))
    conn.commit()
    conn.close()

# Route to display the products
@app.route('/')
def index():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products')
    products = c.fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Route to add new product (only accessible to admin users)
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        username = request.form.get('username')
        if is_admin(username):
            name = request.form['name']
            price = request.form['price']
            description = request.form['description']
            print(f"Received data: username={username}, name={name}, price={price}, description={description}")
            conn = sqlite3.connect('ecommerce.db')
            c = conn.cursor()
            try:
                c.execute('INSERT INTO products (name, price, description) VALUES (?, ?, ?)', (name, price, description))
                conn.commit()
                conn.close()
                return redirect(url_for('index'))
            except sqlite3.Error as e:
                print("SQLite error:", e)
                return "Error adding product to the database."
        else:
            return "You don't have permission to access this feature."
    return render_template('add_product.html')

# Route to remove a product (only accessible to admin users)
@app.route('/remove_product', methods=['POST'])
def remove_product():
    if is_admin(request.form['username']):
        product_id = request.form['product_id']
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE id=?', (product_id,))
        product = c.fetchone()
        if product:
            c.execute('DELETE FROM products WHERE id=?', (product_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            return "Product does not exist."
    else:
        return "You don't have permission to access this feature."

# Route to modify product information (only accessible to admin users)
@app.route('/modify_product', methods=['POST'])
def modify_product():
    if is_admin(request.form['username']):
        product_id = request.form['product_id']
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE id=?', (product_id,))
        product = c.fetchone()
        if product:
            c.execute('UPDATE products SET name=?, price=?, description=? WHERE id=?', (name, price, description, product_id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            return "Product does not exist."
    else:
        return "You don't have permission to access this feature."

# Function to check if user is admin
def is_admin(username):
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    c.execute('SELECT admin FROM users WHERE username=?', (username,))
    admin = c.fetchone()
    conn.close()
    return bool(admin) and admin[0] == 1

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)