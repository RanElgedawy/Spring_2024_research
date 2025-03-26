from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re

app = Flask(__name__)

def create_database():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS reviews")
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS orders")

    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        rating INTEGER,
        text TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER
    )''')
    conn.commit()
    conn.close()

create_database()

def populate_database():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()

    # Insert a user
    c.execute("INSERT INTO users (username, email, password) VALUES ('user1', 'user1@example.com', 'password123')")

    # Insert a product
    c.execute("INSERT INTO products (name, description, price) VALUES ('Product 1', 'A great product', 9.99)")

    # Insert an order
    c.execute("INSERT INTO orders (user_id, product_id, quantity) VALUES (1, 1, 2)")

    # Insert a review
    c.execute("INSERT INTO reviews (user_id, product_id, rating, text) VALUES (1, 1, 5, 'This is a great product')")

    conn.commit()
    conn.close()

populate_database()

@app.route('/submit_review/<int:product_id>', methods=['POST'])
def submit_review(product_id):
    user_id = 1  # Replace with actual user ID
    rating = request.form['rating']
    text = request.form['text']

    # Validate review input
    if not rating or rating.strip() == "":
        return "Please enter a rating."
    if not text or text.strip() == "":
        return "Please enter a review."

    # Ensure rating is between 1 and 5
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return "Rating must be between 1 and 5."
    except ValueError:
        return "Invalid rating."
    
    # Sanitize user input to prevent SQL injection and XSS
    rating = int(rating)  # Ensure rating is an integer
    text = re.sub(r'[<>]', '', text)  # Remove potential XSS characters

    # Check if the user exists in the users table
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        return "User not found"

    # Check if the product exists in the products table
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()

    if not product:
        return "Product not found"

    # Check if the user has purchased the product in the orders table
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    order = c.fetchone()
    conn.close()

    if not order:
        return "User has not purchased this product"

    # Insert review into database
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("INSERT INTO reviews (user_id, product_id, rating, text) VALUES (?, ?, ?, ?)",
              (user_id, product_id, rating, text))
    conn.commit()
    conn.close()

    return redirect(url_for('product_page', product_id=product_id))

@app.route('/product/<int:product_id>')
def product_page(product_id):
    # Retrieve product details from the products table
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()

    # Retrieve reviews for the product
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT rating, text FROM reviews WHERE product_id = ?", (product_id,))
    reviews = c.fetchall()
    conn.close()

    return render_template('product.html', product=product, reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)