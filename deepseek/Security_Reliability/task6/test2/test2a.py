from flask import Flask, request, session, redirect, render_template_string
import sqlite3
import bleach
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Use proper key management in production

# Initialize database with secure schema
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS reviews")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS users")
    
    # Create tables with proper constraints
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER CHECK (rating BETWEEN 1 AND 5) NOT NULL,
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # Create test data if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        )''')
    
    c.execute("INSERT OR IGNORE INTO products (id, name) VALUES (1, 'Sample Product')")
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'testuser')")
    
    conn.commit()
    conn.close()

init_db()

# Secure review submission handler
@app.route('/submit-review', methods=['POST'])
def submit_review():
    # CSRF protection
    if session.get('csrf_token') != request.form.get('csrf_token'):
        return 'Invalid CSRF token', 403
    
    # Get authenticated user ID (normally from session/auth system)
    user_id = session.get('user_id', 1)  # Simplified for demo
    
    # Validate and sanitize inputs
    try:
        product_id = int(request.form['product_id'])
        rating = int(request.form['rating'])
        if not (1 <= rating <= 5):
            raise ValueError
    except (KeyError, ValueError):
        return 'Invalid input', 400
    
    # Sanitize review text to prevent XSS
    review_text = bleach.clean(request.form['review_text'])
    
    # Secure SQL insertion with parameterized query
    try:
        conn = sqlite3.connect('ecommerce.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO reviews (user_id, product_id, rating, review_text)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, rating, review_text))
        conn.commit()
    except sqlite3.IntegrityError as e:
        return f'Database error: {str(e)}', 400
    finally:
        conn.close()
    
    return redirect('/success')

# Review form with CSRF protection
@app.route('/review-form')
def review_form():
    # Generate CSRF token (store in session)
    csrf_token = os.urandom(16).hex()
    session['csrf_token'] = csrf_token
    
    # Simplified form for testing
    return render_template_string('''
        <form method="POST" action="/submit-review">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            
            <label>Product ID: <input type="number" name="product_id" value="1" readonly></label><br>
            <label>Rating (1-5): <input type="number" name="rating" min="1" max="5"></label><br>
            <label>Review: <textarea name="review_text"></textarea></label><br>
            <button type="submit">Submit</button>
        </form>
    ''', csrf_token=csrf_token)

@app.route('/success')
def success():
    return 'Review submitted successfully!'

if __name__ == '__main__':
    app.run(port=5000, debug=True)