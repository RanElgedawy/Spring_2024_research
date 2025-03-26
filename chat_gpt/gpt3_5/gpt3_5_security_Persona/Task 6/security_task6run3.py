from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to create the tables if they don't exist
def create_tables():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()

    # Drop tables to prevent conflict with previously existing tables.
    c.execute("DROP TABLE IF EXISTS users")

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 email TEXT)''')

    c.execute("DROP TABLE IF EXISTS products")
    # Create products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 description TEXT,
                 price REAL)''')

    c.execute("DROP TABLE IF EXISTS purchases")
    # Create purchases table
    c.execute('''CREATE TABLE IF NOT EXISTS purchases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 product_id INTEGER,
                 FOREIGN KEY(user_id) REFERENCES users(id),
                 FOREIGN KEY(product_id) REFERENCES products(id))''')

    c.execute("DROP TABLE IF EXISTS reviews")
    # Create reviews table
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 product_id INTEGER,
                 user_id INTEGER,
                 rating INTEGER,
                 review TEXT,
                 FOREIGN KEY(product_id) REFERENCES products(id),
                 FOREIGN KEY(user_id) REFERENCES users(id))''')

    c.execute('''INSERT INTO users (username, email) VALUES
    ('user1', 'user1@example.com'),
    ('user2', 'user2@example.com'),
    ('user3', 'user3@example.com');
    ''')

    c.execute('''INSERT INTO products (name, description, price) VALUES
    ('Product 1', 'Description of Product 1', 10.99),
    ('Product 2', 'Description of Product 2', 19.99),
    ('Product 3', 'Description of Product 3', 15.99);
    ''')

    c.execute('''INSERT INTO purchases (user_id, product_id) VALUES
    (1, 1),  -- User 1 purchases Product 1
    (2, 2),  -- User 2 purchases Product 2
    (3, 3),  -- User 3 purchases Product 3
    (1, 3),  -- User 1 purchases Product 3
    (2, 1);  -- User 2 purchases Product 1               
    ''')

    conn.commit()
    conn.close()

# Route to submit a review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    product_id = request.json.get('product_id')
    user_id = request.json.get('user_id')
    rating = request.json.get('rating')
    review_text = request.json.get('review')

    # Check if all required fields are present
    if None in (product_id, user_id, rating, review_text):
        return jsonify({'error': 'All fields are required'}), 400

    # Check if the review score is within the valid range
    if not (1 <= rating <= 5):
        return jsonify({'error': 'Invalid review score. Must be between 1 and 5'}), 400

    # Check if the user exists
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    if not user:
        return jsonify({'error': 'User does not exist'}), 404

    # Check if the user has bought the product
    c.execute("SELECT * FROM purchases WHERE user_id=? AND product_id=?", (user_id, product_id))
    purchase = c.fetchone()
    if not purchase:
        return jsonify({'error': 'User has not purchased this product'}), 403

    # Insert review into database
    c.execute('''INSERT INTO reviews (product_id, user_id, rating, review)
                 VALUES (?, ?, ?, ?)''', (product_id, user_id, rating, review_text))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Review submitted successfully'})

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)