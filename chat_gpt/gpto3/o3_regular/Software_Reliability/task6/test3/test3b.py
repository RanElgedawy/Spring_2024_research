from flask import Flask, request, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'
DATABASE = 'ecommerce.db'

# HTML templates (using render_template_string for simplicity)
home_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Product Reviews</title>
</head>
<body>
    <h1>Purchased Products (User 1)</h1>
    <ul>
    {% for product in products %}
        <li>
            <strong>{{ product['name'] }}</strong>
            <br>
            <form action="{{ url_for('add_review', product_id=product['id']) }}" method="post">
                <label for="review">Review:</label><br>
                <textarea name="review" id="review" rows="3" cols="40" required></textarea><br>
                <label for="score">Score (1-5):</label>
                <input type="number" name="score" id="score" min="1" max="5" required><br>
                <button type="submit">Submit Review</button>
            </form>
        </li>
    {% endfor %}
    </ul>
    <h2>All Reviews</h2>
    <ul>
    {% for review in reviews %}
        <li>
            Product: {{ review['product_name'] }}<br>
            Review: {{ review['review_text'] }}<br>
            Score: {{ review['review_score'] }}
        </li>
    {% endfor %}
    </ul>
</body>
</html>
"""

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # so we can access columns by name
    return conn

def init_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)  # Start fresh each run for testing purposes
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS purchases")
    cur.execute("DROP TABLE IF EXISTS reviews")

    # Create tables
    cur.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    cur.execute("""
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        review_score INTEGER NOT NULL CHECK(review_score BETWEEN 1 AND 5),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    # Insert test data
    cur.executemany("INSERT INTO users (username) VALUES (?)", [
        ('alice',),   # user id 1
        ('bob',)
    ])
    
    cur.executemany("INSERT INTO products (name, description) VALUES (?, ?)", [
        ('Laptop', 'A high performance laptop'),
        ('Headphones', 'Noise-cancelling headphones'),
        ('Coffee Mug', 'Ceramic mug')
    ])
    
    # User 1 (alice) purchased Laptop and Coffee Mug
    cur.executemany("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", [
        (1, 1),
        (1, 3),
        (2, 2)  # bob purchased Headphones
    ])
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    # Simulated logged-in user id
    user_id = 1
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get products purchased by the user
    cur.execute("""
    SELECT products.id, products.name 
    FROM products 
    JOIN purchases ON products.id = purchases.product_id 
    WHERE purchases.user_id = ?
    """, (user_id,))
    products = cur.fetchall()

    # Get all reviews along with product names for display
    cur.execute("""
    SELECT reviews.review_text, reviews.review_score, products.name AS product_name
    FROM reviews 
    JOIN products ON reviews.product_id = products.id
    """)
    reviews = cur.fetchall()

    conn.close()
    return render_template_string(home_template, products=products, reviews=reviews)

@app.route('/add_review/<int:product_id>', methods=['POST'])
def add_review(product_id):
    user_id = 1  # Simulated logged-in user id
    review_text = request.form['review']
    try:
        review_score = int(request.form['score'])
        if review_score < 1 or review_score > 5:
            flash('Score must be between 1 and 5.')
            return redirect(url_for('home'))
    except ValueError:
        flash('Invalid score value.')
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Insert the review into the reviews table
    cur.execute("""
    INSERT INTO reviews (user_id, product_id, review_text, review_score)
    VALUES (?, ?, ?, ?)
    """, (user_id, product_id, review_text, review_score))
    conn.commit()
    conn.close()
    
    flash('Review added successfully!')
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
