from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'


def get_db():
    """Open a connection to the SQLite database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database with required tables."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create tables for users, products, purchases, and reviews
        cursor.executescript('''
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS purchases;
        DROP TABLE IF EXISTS reviews;
        
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            review_text TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        ''')

        db.commit()
        print("Database initialized.")


@app.route('/add_review', methods=['POST'])
def add_review():
    """Endpoint to add a review for a purchased product."""
    try:
        user_id = request.json.get('user_id')
        product_id = request.json.get('product_id')
        rating = request.json.get('rating')
        review_text = request.json.get('review_text')

        # Basic validation
        if not (1 <= rating <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5.'}), 400

        # Check if the user has purchased the product
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT id FROM purchases WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        purchase = cursor.fetchone()

        if not purchase:
            return jsonify({'error': 'User has not purchased this product.'}), 400

        # Insert the review
        cursor.execute(
            'INSERT INTO reviews (user_id, product_id, rating, review_text) VALUES (?, ?, ?, ?)',
            (user_id, product_id, rating, review_text)
        )
        db.commit()

        return jsonify({'message': 'Review added successfully.'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/test_setup', methods=['GET'])
def test_setup():
    """Test function to populate the database with some sample data."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Insert sample users
        cursor.execute('INSERT OR IGNORE INTO users (username) VALUES (?)', ('john_doe',))
        cursor.execute('INSERT OR IGNORE INTO users (username) VALUES (?)', ('jane_doe',))

        # Insert sample products
        cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', ('Laptop',))
        cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', ('Smartphone',))

        # Insert sample purchases
        cursor.execute('INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (?, ?)', (1, 1))
        cursor.execute('INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (?, ?)', (2, 2))

        db.commit()

        return jsonify({'message': 'Sample data added successfully.'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Run the app
    app.run(debug=True)