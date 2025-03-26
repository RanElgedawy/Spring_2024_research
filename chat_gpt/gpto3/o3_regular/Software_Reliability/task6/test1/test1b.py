import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = 'app.db'

def init_db():
    """Initializes the database and creates tables if they do not exist.
       Also inserts some sample data for users, products, and purchases."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create users table
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS purchases")
    c.execute("DROP TABLE IF EXISTS reviews")

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')
    # Create products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    # Create purchases table (records that a user purchased a product)
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    # Create reviews table to store user reviews
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT,
            review_score INTEGER CHECK(review_score BETWEEN 1 AND 5),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Insert sample data for testing purposes
    # A sample user with id 1 (if not already present)
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'testuser')")
    # Sample products with ids 1 and 2
    c.execute("INSERT OR IGNORE INTO products (id, name) VALUES (1, 'Product 1')")
    c.execute("INSERT OR IGNORE INTO products (id, name) VALUES (2, 'Product 2')")
    # Record that the sample user purchased these products
    c.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 1)")
    c.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 2)")
    
    conn.commit()
    conn.close()

@app.route('/add_review', methods=['POST'])
def add_review():
    """
    Expects a JSON payload with:
      - user_id: integer
      - product_id: integer
      - review_text: string (optional)
      - review_score: integer (must be between 1 and 5)
      
    It first checks that the user has purchased the product and then saves the review.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    review_text = data.get('review_text', '')
    review_score = data.get('review_score')

    # Validate review score
    if not isinstance(review_score, int) or review_score < 1 or review_score > 5:
        return jsonify({'error': 'Review score must be an integer between 1 and 5'}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Check if the user has purchased the product
    c.execute("SELECT id FROM purchases WHERE user_id=? AND product_id=?", (user_id, product_id))
    purchase = c.fetchone()
    if not purchase:
        conn.close()
        return jsonify({'error': 'User has not purchased this product'}), 400

    # Insert the review into the database
    c.execute("""
        INSERT INTO reviews (user_id, product_id, review_text, review_score)
        VALUES (?, ?, ?, ?)
    """, (user_id, product_id, review_text, review_score))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Review added successfully'})

@app.route('/reviews', methods=['GET'])
def list_reviews():
    """A simple endpoint to list all reviews for testing purposes."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, user_id, product_id, review_text, review_score FROM reviews")
    reviews = c.fetchall()
    conn.close()
    return jsonify({'reviews': reviews})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
