from flask import Flask, request, g, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS purchases")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        # Create tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            username TEXT NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            product_id INTEGER,
                            FOREIGN KEY(user_id) REFERENCES users(id),
                            FOREIGN KEY(product_id) REFERENCES products(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            product_id INTEGER,
                            review_text TEXT,
                            review_score INTEGER CHECK(review_score BETWEEN 1 AND 5),
                            FOREIGN KEY(user_id) REFERENCES users(id),
                            FOREIGN KEY(product_id) REFERENCES products(id))''')

        db.commit()

@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    review_text = request.json.get('review_text')
    review_score = request.json.get('review_score')

    if not (user_id and product_id and review_score and 1 <= review_score <= 5):
        return jsonify({"error": "Invalid input"}), 400

    db = get_db()
    cursor = db.cursor()

    # Check if the user has purchased the product
    cursor.execute("SELECT 1 FROM purchases WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    purchase = cursor.fetchone()

    if not purchase:
        return jsonify({"error": "User has not purchased this product"}), 403

    # Insert the review
    cursor.execute("INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)",
                   (user_id, product_id, review_text, review_score))
    db.commit()

    return jsonify({"message": "Review added successfully"}), 201

@app.route('/init_db', methods=['GET'])
def initialize_db():
    init_db()
    return jsonify({"message": "Database initialized"}), 200

@app.route('/test_data', methods=['GET'])
def add_test_data():
    db = get_db()
    cursor = db.cursor()

    # Add some users
    cursor.execute("INSERT INTO users (username) VALUES ('user1')")
    cursor.execute("INSERT INTO users (username) VALUES ('user2')")

    # Add some products
    cursor.execute("INSERT INTO products (name) VALUES ('Product 1')")
    cursor.execute("INSERT INTO products (name) VALUES ('Product 2')")

    # Simulate purchases
    cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 1)")
    cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 2)")
    cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (2, 1)")

    db.commit()
    return jsonify({"message": "Test data added"}), 200

if __name__ == '__main__':
    app.run(debug=True)