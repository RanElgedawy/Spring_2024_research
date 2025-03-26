from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Database setup
DATABASE = 'ecommerce.db'

def create_tables():
    """Create tables in the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        # Create table for users (for demonstration purposes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
        ''')
        # Create table for products (for demonstration purposes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Create table for orders (to link users and products)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        # Create table for reviews
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT,
                review_score INTEGER NOT NULL CHECK(review_score >= 1 AND review_score <= 5),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        conn.commit()

# Call the function to create tables
create_tables()

# Add a review
@app.route('/add_review', methods=['POST'])
def add_review():
    """Add a review for a purchased product."""
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    review_text = data.get('review_text')
    review_score = data.get('review_score')

    # Check if the user has purchased the product
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        order = cursor.fetchone()

        if not order:
            return jsonify({'error': 'User has not purchased this product.'}), 400

        # Insert the review
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score))
        conn.commit()

    return jsonify({'message': 'Review added successfully'}), 201

# Get all reviews for a product
@app.route('/product_reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    """Get all reviews for a given product."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, review_text, review_score FROM reviews WHERE product_id = ?', (product_id,))
        reviews = cursor.fetchall()

    return jsonify({'reviews': [{'user_id': r[0], 'review_text': r[1], 'review_score': r[2]} for r in reviews]})

def insert_test_data():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Insert users
        cursor.execute("INSERT INTO users (username) VALUES ('Alice')")
        cursor.execute("INSERT INTO users (username) VALUES ('Bob')")

        # Insert products
        cursor.execute("INSERT INTO products (name) VALUES ('Laptop')")
        cursor.execute("INSERT INTO products (name) VALUES ('Smartphone')")

        # Insert orders (linking users with products)
        cursor.execute("INSERT INTO orders (user_id, product_id) VALUES (1, 1)")
        cursor.execute("INSERT INTO orders (user_id, product_id) VALUES (2, 2)")

        conn.commit()

insert_test_data()

if __name__ == '__main__':
    app.run(debug=True)