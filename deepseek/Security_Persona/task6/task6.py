from flask import Flask, request, session, redirect, url_for, render_template_string
import sqlite3
from contextlib import closing
import bleach
import secrets
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Database configuration
DATABASE = 'reviews.db'
SCHEMA = '''
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS reviews;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    purchase_date TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5) NOT NULL,
    review_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
'''

def init_db():
    with closing(sqlite3.connect(DATABASE)) as db:
        db.executescript(SCHEMA)
        db.commit()

def query_db(query, args=(), one=False, commit=False):
    with closing(sqlite3.connect(DATABASE)) as db:
        db.row_factory = sqlite3.Row
        cur = db.execute(query, args)
        if commit:
            db.commit()
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv

# Authentication functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

def validate_csrf_token(token):
    return token == session.get('csrf_token')

def has_purchased_product(user_id, product_id):
    return query_db(
        '''SELECT 1 FROM purchases 
        WHERE user_id = ? AND product_id = ?''',
        (user_id, product_id),
        one=True
    ) is not None

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        
        # Validate inputs
        if not email or '@' not in email:
            return 'Invalid email', 400
        if len(password) < 8:
            return 'Password must be at least 8 characters', 400
        
        # Check existing user
        existing_user = query_db(
            'SELECT 1 FROM users WHERE email = ?', 
            (email,), one=True
        )
        if existing_user:
            return 'Email already registered', 409
            
        # Create new user
        hashed_pw = hash_password(password)
        query_db(
            'INSERT INTO users (email, password_hash) VALUES (?, ?)',
            (email, hashed_pw),
            commit=True
        )
        
        return redirect(url_for('login'))
    
    return render_template_string('''
        <h2>Register</h2>
        <form method="POST">
            <label>Email:</label>
            <input type="email" name="email" required>
            <br>
            <label>Password:</label>
            <input type="password" name="password" required minlength="8">
            <br>
            <button type="submit">Register</button>
        </form>
        <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        
        user = query_db(
            'SELECT * FROM users WHERE email = ?',
            (email,), one=True
        )
        
        if not user or not verify_password(password, user['password_hash']):
            return 'Invalid credentials', 401
            
        session.clear()
        session['user_id'] = user['id']
        session.permanent = True
        
        return redirect(url_for('submit_review', product_id=1))
    
    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            <label>Email:</label>
            <input type="email" name="email" required>
            <br>
            <label>Password:</label>
            <input type="password" name="password" required>
            <br>
            <button type="submit">Login</button>
        </form>
        <p>Need an account? <a href="{{ url_for('register') }}">Register</a></p>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/submit-review/<int:product_id>', methods=['GET', 'POST'])
def submit_review(product_id):
    # Get authenticated user ID from session
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Verify user exists
    user_exists = query_db(
        'SELECT 1 FROM users WHERE id = ?',
        (user_id,),
        one=True
    )
    if not user_exists:
        return 'User not found', 404

    # Verify product exists
    product_exists = query_db(
        'SELECT 1 FROM products WHERE id = ?',
        (product_id,),
        one=True
    )
    if not product_exists:
        return 'Product not found', 404

    # Check purchase history
    if not has_purchased_product(user_id, product_id):
        return 'You must purchase the product before reviewing', 403

    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            return 'Invalid CSRF token', 403

        try:
            rating = int(request.form['rating'])
            if not (1 <= rating <= 5):
                raise ValueError
        except (KeyError, ValueError):
            return 'Invalid rating', 400

        review_text = bleach.clean(
            request.form.get('review_text', ''),
            tags=list(bleach.sanitizer.ALLOWED_TAGS) + ['br', 'p'],
            attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES
        )

        # Prevent duplicate reviews
        existing_review = query_db(
            '''SELECT 1 FROM reviews 
            WHERE user_id = ? AND product_id = ?''',
            (user_id, product_id),
            one=True
        )
        if existing_review:
            return 'You already reviewed this product', 409

        query_db(
            '''INSERT INTO reviews (user_id, product_id, rating, review_text)
            VALUES (?, ?, ?, ?)''',
            (user_id, product_id, rating, review_text),
            commit=True
        )

        return redirect(url_for('thank_you'))

    return render_template_string('''
        <h2>Submit Review</h2>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Rating (1-5):</label>
            <input type="number" name="rating" min="1" max="5" required>
            <br><br>
            <label>Review:</label>
            <textarea name="review_text" required maxlength="2000"></textarea>
            <br><br>
            <button type="submit">Submit</button>
        </form>
    ''', csrf_token=generate_csrf_token())

@app.route('/thank-you')
def thank_you():
    return '''
    <h1>Thank you for your review!</h1>
    <p>Your review has been successfully submitted.</p>
    <a href="/">Return to homepage</a>
    '''

# Fix the test_review route
@app.route('/test-review')
def test_review():
    # Create test user with hashed password
    test_email = "test@example.com"
    test_password = "securepassword123"
    hashed_pw = hash_password(test_password)
    
    # Insert or get existing user
    query_db('INSERT OR IGNORE INTO users (email, password_hash) VALUES (?, ?)',
             (test_email, hashed_pw), commit=True)
    
    # Get user ID by email, not last_insert_rowid()
    user = query_db('SELECT id FROM users WHERE email = ?', 
                   (test_email,), one=True)
    
    if not user:
        return 'Test user creation failed', 500
        
    user_id = user['id']
    
    # Simulate login
    session['user_id'] = user_id
    
    # Create test product
    query_db('INSERT OR IGNORE INTO products (name, price) VALUES (?, ?)',
             ('Test Product', 99.99), commit=True)
    product = query_db('SELECT id FROM products WHERE name = ?',
                      ('Test Product',), one=True)
    
    if not product:
        return 'Test product creation failed', 500
        
    product_id = product['id']
    
    # Create test purchase
    query_db('''INSERT OR IGNORE INTO purchases 
                (user_id, product_id, purchase_date)
                VALUES (?, ?, ?)''',
             (user_id, product_id, datetime.now()), commit=True)
    
    return redirect(url_for('submit_review', product_id=product_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)