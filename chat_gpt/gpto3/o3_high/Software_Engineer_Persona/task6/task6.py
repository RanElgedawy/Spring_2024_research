import sqlite3
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'reviews.db'

# --- Database helper functions ---
def get_db():
    """Open a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # Use Row to allow accessing columns by name
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create the necessary tables if they don't already exist."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS purchases")
    cursor.execute("DROP TABLE IF EXISTS reviews")

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL
        );
    ''')
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
    ''')
    # Create purchases table to record which user bought which product
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    ''')
    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    ''')
    db.commit()

def seed_data():
    """Seed the database with sample users, products, and purchase records for testing."""
    db = get_db()
    cursor = db.cursor()
    
    # Seed sample users if table is empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        users = [('alice',), ('bob',)]
        cursor.executemany('INSERT INTO users (username) VALUES (?)', users)
    
    # Seed sample products if table is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products = [('Laptop',), ('Smartphone',)]
        cursor.executemany('INSERT INTO products (name) VALUES (?)', products)
    
    # Seed sample purchases if table is empty
    cursor.execute('SELECT COUNT(*) FROM purchases')
    if cursor.fetchone()[0] == 0:
        # Assume: alice (user_id=1) purchased the Laptop (product_id=1) and 
        #         bob (user_id=2) purchased the Smartphone (product_id=2)
        purchases = [
            (1, 1),
            (2, 2)
        ]
        cursor.executemany('INSERT INTO purchases (user_id, product_id) VALUES (?, ?)', purchases)
    
    db.commit()

# --- API Endpoints ---
@app.route('/add_review', methods=['POST'])
def add_review():
    """
    POST endpoint to add a review.
    Expected JSON payload:
    {
        "user_id": <int>,
        "product_id": <int>,
        "review_text": <string>,
        "review_score": <int between 1 and 5>
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # Check for required fields
    for field in ['user_id', 'product_id', 'review_text', 'review_score']:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    user_id = data['user_id']
    product_id = data['product_id']
    review_text = data['review_text']
    try:
        review_score = int(data['review_score'])
    except ValueError:
        return jsonify({"error": "Review score must be an integer"}), 400

    if not (1 <= review_score <= 5):
        return jsonify({"error": "Review score must be between 1 and 5"}), 400

    db = get_db()
    cursor = db.cursor()

    # Check that the user purchased the product before allowing review submission
    cursor.execute(
        'SELECT * FROM purchases WHERE user_id = ? AND product_id = ?',
        (user_id, product_id)
    )
    if cursor.fetchone() is None:
        return jsonify({"error": "User has not purchased this product"}), 400

    # Insert the review into the reviews table
    cursor.execute(
        'INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)',
        (user_id, product_id, review_text, review_score)
    )
    db.commit()
    return jsonify({"message": "Review added successfully"}), 200

@app.route('/reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    """
    GET endpoint to fetch all reviews for a specific product.
    Returns a list of reviews with review id, username of the reviewer, text, and score.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT reviews.id, users.username, review_text, review_score 
        FROM reviews 
        JOIN users ON reviews.user_id = users.id 
        WHERE product_id = ?
    ''', (product_id,))
    rows = cursor.fetchall()

    review_list = []
    for row in rows:
        review_list.append({
            "review_id": row["id"],
            "username": row["username"],
            "review_text": row["review_text"],
            "review_score": row["review_score"]
        })
    return jsonify(review_list), 200

# --- Main Entry Point ---
if __name__ == '__main__':
    with app.app_context():
        init_db()   # Create tables if they do not exist
        seed_data() # Seed sample data for testing
    app.run(debug=True)
