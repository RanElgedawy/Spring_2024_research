from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Function to initialize the database and create the necessary tables
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS reviews")


        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )
        ''')
        # Create products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        ''')
        # Create reviews table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT,
            review_score INTEGER CHECK(review_score BETWEEN 1 AND 5),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        conn.commit()

# Initialize the database
init_db()

# Route to add a new review
@app.route('/add_review', methods=['POST'])
def add_review():
    try:
        # Extract data from request
        user_id = request.json.get('user_id')
        product_id = request.json.get('product_id')
        review_text = request.json.get('review_text')
        review_score = request.json.get('review_score')

        # Validate the input
        if not (1 <= review_score <= 5):
            return jsonify({'error': 'Review score must be between 1 and 5'}), 400

        # Check if the user has purchased the product
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM purchases WHERE user_id = ? AND product_id = ?', (user_id, product_id))
            purchase = cursor.fetchone()
            if not purchase:
                return jsonify({'error': 'User has not purchased this product'}), 400

            # Insert the review into the reviews table
            cursor.execute(
                'INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)',
                (user_id, product_id, review_text, review_score)
            )
            conn.commit()

        return jsonify({'message': 'Review added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to get all reviews for a product
@app.route('/product_reviews/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,))
            reviews = cursor.fetchall()
            reviews_list = [dict(review) for review in reviews]
        return jsonify(reviews_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sample data for testing
@app.route('/init_sample_data', methods=['GET'])
def init_sample_data():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Insert sample users
            cursor.execute('INSERT INTO users (username) VALUES (?)', ('Alice',))
            cursor.execute('INSERT INTO users (username) VALUES (?)', ('Bob',))

            # Insert sample products
            cursor.execute('INSERT INTO products (name) VALUES (?)', ('Laptop',))
            cursor.execute('INSERT INTO products (name) VALUES (?)', ('Smartphone',))

            # Insert sample purchases
            cursor.execute("DROP TABLE IF EXISTS purchases")
            cursor.execute('CREATE TABLE IF NOT EXISTS purchases (user_id INTEGER, product_id INTEGER)')
            cursor.execute('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', (1, 1))  # Alice bought Laptop
            cursor.execute('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', (2, 2))  # Bob bought Smartphone

            conn.commit()
        return jsonify({'message': 'Sample data initialized'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)