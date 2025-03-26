from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import os
import hashlib
import hmac
import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'reviews.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_tables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        ''')

        # Create products table (assuming it doesn't already exist)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL
            )
        ''')

        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Create reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL,
                csrf_token TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Insert test users
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', ('testuser', 'hashedpassword'))
    
        # Insert test products
        cursor.execute('INSERT INTO products (product_name) VALUES (?)', ('Test Product',))
    
        # Get the IDs of the inserted user and product
        cursor.execute('SELECT id FROM users WHERE username = ?', ('testuser',))
        user_id = cursor.fetchone()[0]

        cursor.execute('SELECT id FROM products WHERE product_name = ?', ('Test Product',))
        product_id = cursor.fetchone()[0]

        # Insert test order
        cursor.execute('INSERT INTO orders (user_id, product_id) VALUES (?, ?)', (user_id, product_id))
        db.commit()

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        user_id = request.form['user_id']  # Retrieve user_id from the form data
        product_id = request.form['product_id']
        review_text = request.form['review_text'].strip()
        rating = request.form['rating']
        csrf_token = request.form['csrf_token']

        # Validate CSRF token
        if not validate_csrf(csrf_token):
            return jsonify({'error': 'Invalid CSRF token'}), 400

        # Check if review text and rating are provided
        if not review_text:
            return jsonify({'error': 'Review text cannot be empty'}), 400
        if not rating:
            return jsonify({'error': 'Rating is required'}), 400

        # Basic validation for rating value
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        except ValueError:
            return jsonify({'error': 'Rating must be a number between 1 and 5'}), 400

        # Validate user and purchase
        if not validate_user_purchase(user_id, product_id):
            return jsonify({'error': 'User does not exist or has not purchased this product'}), 403

        # Sanitize inputs to prevent XSS
        review_text = sanitize_input(review_text)

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, rating, csrf_token)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, product_id, review_text, rating, csrf_token))
        db.commit()
        return jsonify({'success': 'Review submitted successfully'})

    # Generate CSRF token
    csrf_token = generate_csrf()
    return render_template('submit_review.html', csrf_token=csrf_token)

def validate_user_purchase(user_id, product_id):
    db = get_db()
    cursor = db.cursor()

    # Check if the user exists
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        return False

    # Check if the user has purchased the product
    cursor.execute('''
        SELECT id FROM orders WHERE user_id = ? AND product_id = ?
    ''', (user_id, product_id))
    purchase_exists = cursor.fetchone()

    return purchase_exists is not None

def sanitize_input(input_text):
    return input_text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;").replace("\"", "&quot;").replace("'", "&#x27;")

def generate_csrf():
    session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

def validate_csrf(csrf_token):
    return csrf_token == session.get('csrf_token')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)