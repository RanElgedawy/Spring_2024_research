from flask import Flask, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute("DROP TABLE IF EXISTS purchases")
    conn.execute("DROP TABLE IF EXISTS reviews")

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        )''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            user_id INTEGER,
            product_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            review_text TEXT,
            review_score INTEGER CHECK(review_score BETWEEN 1 AND 5),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')
    conn.close()

create_tables()

@app.route('/submit_review', methods=['POST'])
def submit_review():
    try:
        user_id = int(request.form['user_id'])
        product_id = int(request.form['product_id'])
        review_text = request.form['review_text']
        review_score = int(request.form['review_score'])
    except ValueError:
        return "Invalid input data", 400

    if not (1 <= review_score <= 5):
        return "Rating must be between 1 and 5", 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Verify purchase
    cursor.execute('''
        SELECT 1 FROM purchases 
        WHERE user_id = ? AND product_id = ?
    ''', (user_id, product_id))
    if not cursor.fetchone():
        conn.close()
        return "You can only review purchased products", 403

    # Insert review
    try:
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, review_score))
        conn.commit()
        conn.close()
        return "Review submitted successfully!", 201
    except sqlite3.Error as e:
        conn.close()
        return f"Database error: {str(e)}", 500

@app.route('/test', methods=['GET', 'POST'])
def test_review():
    # Create test data
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'test_user')")
    conn.execute("INSERT OR IGNORE INTO products (id, name) VALUES (1, 'Test Product')")
    conn.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 1)")
    conn.commit()
    conn.close()

    # Simple test form
    return '''
        <h2>Test Review Submission</h2>
        <form method="POST" action="/submit_review">
            <input type="hidden" name="user_id" value="1">
            <input type="hidden" name="product_id" value="1">
            <p>Review Text: <textarea name="review_text"></textarea></p>
            <p>Rating (1-5): <input type="number" name="review_score" min="1" max="5"></p>
            <button type="submit">Submit Review</button>
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)