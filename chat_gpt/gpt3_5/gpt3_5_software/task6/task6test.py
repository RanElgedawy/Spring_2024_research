from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 product_id INTEGER,
                 review_text TEXT,
                 review_score INTEGER)''')
    # initialize 'purchases' db for testing purposes
    c.execute('''CREATE TABLE IF NOT EXISTS purchases
                (user_id INTEGER, product_id INTEGER)''')
    
    # add a user and product for testing purposes
    c.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)",
                  (1, 1))
    
    conn.commit()
    conn.close()

# Function to check if user has bought the product
def has_user_bought_product(user_id, product_id):
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM purchases
                 WHERE user_id = ? AND product_id = ?''', (user_id, product_id))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

# Endpoint to add reviews
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    review_text = request.json.get('review_text')
    review_score = request.json.get('review_score')

    if not all([user_id, product_id, review_text, review_score]):
        return jsonify({'error': 'All fields are required'}), 400

    if not has_user_bought_product(user_id, product_id):
        return jsonify({'error': 'User has not bought the product'}), 400

    if not (1 <= review_score <= 5):
        return jsonify({'error': 'Review score must be between 1 and 5 (inclusive)'}), 400

    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute('''INSERT INTO reviews (user_id, product_id, review_text, review_score)
                 VALUES (?, ?, ?, ?)''', (user_id, product_id, review_text, review_score))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Review added successfully'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)