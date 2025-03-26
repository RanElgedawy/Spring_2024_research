from flask import Flask, request, g, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

# Function to get the database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Initialize the database with necessary tables
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create tables if they don't exist
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT,
            review_score INTEGER CHECK(review_score >= 1 AND review_score <= 5),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')

        # Insert test data for users
        cursor.execute('''
        INSERT INTO users (username) VALUES
        ('Alice'),
        ('Bob'),
        ('Charlie')
        ''')
        
        # Insert test data for products
        cursor.execute('''
        INSERT INTO products (name) VALUES
        ('Product A'),
        ('Product B'),
        ('Product C')
        ''')
        db.commit()

# Clean up database connection after each request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Route for submitting a review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    user_id = request.form['user_id']
    product_id = request.form['product_id']
    review_text = request.form.get('review_text', '')
    review_score = int(request.form['review_score'])
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO reviews (user_id, product_id, review_text, review_score)
        VALUES (?, ?, ?, ?)
    ''', (user_id, product_id, review_text, review_score))
    db.commit()
    
    return jsonify({'message': 'Review submitted successfully'}), 201

# Route for testing the form submission
@app.route('/test_form')
def test_form():
    return render_template_string('''
        <h2>Submit a Review</h2>
        <form action="/submit_review" method="post">
            <label>User ID:</label><br>
            <input type="number" name="user_id" required><br><br>
            <label>Product ID:</label><br>
            <input type="number" name="product_id" required><br><br>
            <label>Review Text:</label><br>
            <textarea name="review_text"></textarea><br><br>
            <label>Review Score (1-5):</label><br>
            <input type="number" name="review_score" min="1" max="5" required><br><br>
            <input type="submit" value="Submit Review">
        </form>
    ''')

# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(debug=True)