from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the database tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS orders")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            shipping_address TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL,
            order_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Retrieve user's cart items
def get_cart_items(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, c.quantity, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

# Calculate total amount
def calculate_total(items):
    total = sum(item['quantity'] * item['price'] for item in items)
    total += 20  # Add shipping fee
    return total

# Process checkout
def process_checkout(user_id, total_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, total_amount, order_date)
        VALUES (?, ?, ?)
    ''', (user_id, total_amount, datetime.datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()
    # Here you would implement the actual payment processing logic
    # ...
    return True  # Assuming successful payment

# Route for the checkout page
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_id = 1  # Replace with actual user ID
    items = get_cart_items(user_id)
    total_amount = calculate_total(items)

    if request.method == 'POST':
        if process_checkout(user_id, total_amount):
            # Clear the cart after successful checkout
            clear_cart(user_id)
            return redirect(url_for('checkout_success'))
        else:
            return render_template('checkout.html', items=items, total_amount=total_amount, error='Payment failed')

    return render_template('checkout.html', items=items, total_amount=total_amount)

# Route for successful checkout
@app.route('/checkout_success')
def checkout_success():
    return render_template('checkout_success.html')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)