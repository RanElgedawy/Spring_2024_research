from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Connect to the database (create if it doesn't exist)
def get_db_connection():
    conn = sqlite3.connect('reviews.db')
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    return conn

# Create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        text_review TEXT,
        review_score INTEGER
    )''')
    conn.commit()
    conn.close()

# API endpoint to submit a review
@app.route('/reviews', methods=['POST'])
def submit_review():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    text_review = request.json['text_review']
    review_score = request.json['review_score']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO reviews (user_id, product_id, text_review, review_score)
               VALUES (?, ?, ?, ?)''', (user_id, product_id, text_review, review_score))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Review submitted successfully'})

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)