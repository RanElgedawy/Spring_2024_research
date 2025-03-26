from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def init_db():
    # Create the database and tables if they do not exist
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Users table (assuming users are already registered)
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS purchases")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        )
        ''')
        # Products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        ''')
        # Purchases table (tracks which users purchased which products)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            user_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            PRIMARY KEY(user_id, product_id)
        )
        ''')
        # Reviews table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            review_text TEXT NOT NULL,
            review_score INTEGER CHECK(review_score >= 1 AND review_score <= 5),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        ''')
        conn.commit()

@app.route('/add_review', methods=['POST'])
def add_review():
    # Retrieve the posted data
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    review_text = request.json.get('review_text')
    review_score = request.json.get('review_score')

    if not (1 <= review_score <= 5):
        return jsonify({'error': 'Review score must be between 1 and 5.'}), 400

    # Check if the user has purchased this product
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM purchases WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        purchase = cursor.fetchone()
        if not purchase:
            return jsonify({'error': 'User has not purchased this product.'}), 400

        # Insert the review into the database
        cursor.execute('''
        INSERT INTO reviews (user_id, product_id, review_text, review_score)
        VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score))
        conn.commit()

    return jsonify({'message': 'Review added successfully.'}), 201

@app.route('/get_reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    # Retrieve all reviews for the given product
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT users.username, reviews.review_text, reviews.review_score
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE reviews.product_id = ?
        ''', (product_id,))
        reviews = cursor.fetchall()

    return jsonify({'reviews': reviews}), 200

def add_test_data():
    # Add some test users, products, and purchases
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Insert test users
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES ('user1'), ('user2')")
        # Insert test products
        cursor.execute("INSERT OR IGNORE INTO products (name) VALUES ('Product A'), ('Product B')")
        # Insert test purchases
        cursor.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 1), (1, 2), (2, 1)")
        conn.commit()

if __name__ == '__main__':
    init_db()  # Initialize the database and tables
    add_test_data()  # Add some test data
    app.run(debug=True)