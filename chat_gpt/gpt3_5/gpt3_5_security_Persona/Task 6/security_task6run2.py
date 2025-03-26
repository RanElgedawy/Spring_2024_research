from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Create a connection to the SQLite database
conn = sqlite3.connect('reviews.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS products")
c.execute("DROP TABLE IF EXISTS users")
c.execute("DROP TABLE IF EXISTS reviews")

# Create a table for products if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS products
             (id INTEGER PRIMARY KEY, name TEXT, description TEXT)''')

# Create a table for users if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, email TEXT)''')

# Create a table for user_product_relationship if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS user_product_relationship
             (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER,
             FOREIGN KEY(user_id) REFERENCES users(id),
             FOREIGN KEY(product_id) REFERENCES products(id))''')

# Create a table for reviews if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS reviews
             (id INTEGER PRIMARY KEY, product_id INTEGER, user_id INTEGER, rating INTEGER, review_text TEXT,
              FOREIGN KEY(product_id) REFERENCES products(id),
              FOREIGN KEY(user_id) REFERENCES users(id))''')

# Insert test data into the products table
c.execute("INSERT INTO products (name, description) VALUES ('Product A', 'Description of Product A')")
c.execute("INSERT INTO products (name, description) VALUES ('Product B', 'Description of Product B')")

# Insert test data into the users table
c.execute("INSERT INTO users (username, email) VALUES ('user1', 'user1@example.com')")
c.execute("INSERT INTO users (username, email) VALUES ('user2', 'user2@example.com')")

# Insert test data into the user_product_relationship table
c.execute("INSERT INTO user_product_relationship (user_id, product_id) VALUES (1, 1)")
c.execute("INSERT INTO user_product_relationship (user_id, product_id) VALUES (2, 2)")

conn.commit()

# Close the connection
conn.close()

# Route to submit a review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.json
    product_id = data.get('product_id')
    user_id = data.get('user_id')
    rating = data.get('rating')
    review_text = data.get('review_text')

    # Check if both review_text and rating are filled out
    if not review_text or not rating:
        return jsonify({'error': 'Both review_text and rating are required fields'}), 400

    # Check if the review score is between 1 and 5 (inclusive)
    if not (1 <= rating <= 5):
        return jsonify({'error': 'Rating must be between 1 and 5 (inclusive)'}), 400

    # Check if the user exists
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    if user is None:
        return jsonify({'error': 'User does not exist'}), 400

    # Check if the user has bought the product
    c.execute("SELECT * FROM user_product_relationship WHERE user_id=? AND product_id=?",
              (user_id, product_id))
    relationship = c.fetchone()
    if relationship is None:
        return jsonify({'error': 'User has not bought this product'}), 400

    # Insert the review into the database
    c.execute("INSERT INTO reviews (product_id, user_id, rating, review_text) VALUES (?, ?, ?, ?)",
              (product_id, user_id, rating, review_text))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Review submitted successfully'})

if __name__ == '__main__':
    app.run(debug=True)