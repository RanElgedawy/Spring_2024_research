from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Utility function to get a database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database and create tables
def init_db():
    with get_db() as conn:
        conn.executescript('''
            DROP TABLE IF EXISTS users;
                           
            DROP TABLE IF EXISTS products;
                           
            DROP TABLE IF EXISTS purchases;
            
            DROP TABLE IF EXISTS reviews;
                           
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                review_score INTEGER NOT NULL CHECK(review_score BETWEEN 1 AND 5),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
        ''')
        print("Database initialized!")

# Route to add a review
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    review_text = request.json.get('review_text')
    review_score = request.json.get('review_score')

    # Validate inputs
    if not review_text or not isinstance(review_score, int):
        return jsonify({'error': 'Review text and review score must be provided and valid'}), 400

    if not (1 <= review_score <= 5):
        return jsonify({'error': 'Review score must be between 1 and 5'}), 400

    with get_db() as conn:
        # Check if the user has purchased the product
        purchase = conn.execute(
            'SELECT * FROM purchases WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        ).fetchone()

        if purchase is None:
            return jsonify({'error': 'Product not purchased by the user'}), 400

        # Add the review
        conn.execute(
            'INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)',
            (user_id, product_id, review_text, review_score)
        )
        conn.commit()
        return jsonify({'success': 'Review added successfully'}), 201

# Test route to simulate a purchase (for testing purposes only)
@app.route('/test_purchase', methods=['POST'])
def test_purchase():
    user_id = request.json['user_id']
    product_id = request.json['product_id']

    with get_db() as conn:
        conn.execute(
            'INSERT INTO purchases (user_id, product_id) VALUES (?, ?)',
            (user_id, product_id)
        )
        conn.commit()
        return jsonify({'success': 'Test purchase recorded successfully'}), 201

if __name__ == '__main__':
    init_db()
    app.run(debug=True)