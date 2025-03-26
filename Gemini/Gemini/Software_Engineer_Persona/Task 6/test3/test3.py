from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

def create_table(conn):
    sql = "DROP TABLE IF EXISTS users"
    cur = conn.cursor()
    cur.execute(sql)

    sql = "DROP TABLE IF EXISTS orders"
    cur.execute(sql)

    sql = "DROP TABLE IF EXISTS reviews"
    cur.execute(sql)

    sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """
    cur.execute(sql)

    sql = """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER
        )
    """
    cur.execute(sql)

    sql = """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            review TEXT,
            rating INTEGER
        )
    """
    cur.execute(sql)
    cur.execute("INSERT INTO users (name) VALUES ('John Doe')")
    cur.execute("INSERT INTO orders (user_id, product_id) VALUES (1, 1)")

    conn.commit()

@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    review_text = request.json['review']
    rating = request.json['rating']

    # Input validation
    if not review_text:
        return jsonify({'message': 'Review text is required.'})
    if rating is None or rating < 1 or rating > 5:
        return jsonify({'message': 'Rating must be a number between 1 and 5.'})

    conn = create_connection('reviews.db')
    create_table(conn)

    # Check if user exists
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_exists = cur.fetchone()
    if not user_exists:
        return jsonify({'message': 'User does not exist.'})

    # Check if user has purchased the product
    cur.execute("SELECT * FROM orders WHERE user_id = ? AND product_id = ?", (user_id, product_id,))
    purchase_exists = cur.fetchone()
    if not purchase_exists:
        return jsonify({'message': 'User has not purchased this product.'})

    # Save the review
    cur.execute("INSERT INTO reviews (user_id, product_id, review, rating) VALUES (?, ?, ?, ?)",
                (user_id, product_id, review_text, rating))
    conn.commit()

    return jsonify({'message': 'Review added successfully'})

if __name__ == '__main__':
    app.run(debug=True)