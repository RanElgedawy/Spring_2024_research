from flask import Flask, request, g, render_template_string, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secretkey'  # needed for flashing messages

DATABASE = 'ecommerce.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Set row_factory to allow dictionary-like row access
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        g._database = db
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    # Remove existing DB for a fresh start (for testing purposes)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    db = get_db()
    cursor = db.cursor()
    # Create tables
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS purchases")
    cursor.execute("DROP TABLE IF EXISTS reviews")

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    # Insert sample users
    cursor.execute("INSERT INTO users (name) VALUES (?)", ('Alice',))  # id 1 (current logged in user)
    cursor.execute("INSERT INTO users (name) VALUES (?)", ('Bob',))    # id 2
    # Insert sample products
    cursor.execute("INSERT INTO products (name) VALUES (?)", ('Product 1',))  # id 1
    cursor.execute("INSERT INTO products (name) VALUES (?)", ('Product 2',))  # id 2
    # Insert sample purchases:
    # Alice purchased Product 1 and Bob purchased Product 2
    cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (1, 1))
    cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (2, 2))
    db.commit()

@app.route('/')
def index():
    # Assume current user is Alice (user_id=1)
    current_user_id = 1
    db = get_db()
    cursor = db.cursor()
    # Retrieve products purchased by Alice
    cursor.execute('''
        SELECT p.id, p.name FROM products p
        INNER JOIN purchases pur ON pur.product_id = p.id
        WHERE pur.user_id = ?
    ''', (current_user_id,))
    products = cursor.fetchall()
    return render_template_string('''
        <h1>Welcome, Alice (User 1)</h1>
        <h2>Your Purchased Products</h2>
        <ul>
        {% for product in products %}
            <li>{{ product['name'] }} - 
                <a href="{{ url_for('add_review', product_id=product['id']) }}">Add Review</a>
            </li>
        {% endfor %}
        </ul>
        <p><a href="{{ url_for('view_reviews') }}">View All Reviews</a></p>
    ''', products=products)

@app.route('/add_review/<int:product_id>', methods=['GET', 'POST'])
def add_review(product_id):
    # For this example, current user is Alice (user_id=1)
    current_user_id = 1
    db = get_db()
    cursor = db.cursor()

    # Validate that the user has purchased the product
    cursor.execute("SELECT * FROM purchases WHERE user_id = ? AND product_id = ?", (current_user_id, product_id))
    purchase = cursor.fetchone()
    if not purchase:
        flash("You haven't purchased this product.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        review_text = request.form.get('review_text', '').strip()
        review_score = request.form.get('review_score', '').strip()

        if not review_text or not review_score:
            flash("Please provide both review text and a review score.")
            return redirect(url_for('add_review', product_id=product_id))

        try:
            review_score = int(review_score)
            if review_score < 1 or review_score > 5:
                flash("Review score must be between 1 and 5.")
                return redirect(url_for('add_review', product_id=product_id))
        except ValueError:
            flash("Invalid review score. Please enter a number between 1 and 5.")
            return redirect(url_for('add_review', product_id=product_id))

        # Save the review to the database
        cursor.execute("""
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        """, (current_user_id, product_id, review_text, review_score))
        db.commit()
        flash("Review added successfully!")
        return redirect(url_for('index'))

    # GET request: show the review form
    return render_template_string('''
        <h1>Add Review for Product {{ product_id }}</h1>
        <form method="post">
            <label for="review_text">Review:</label><br>
            <textarea name="review_text" rows="4" cols="50"></textarea><br><br>
            <label for="review_score">Score (1-5):</label>
            <input type="number" name="review_score" min="1" max="5"><br><br>
            <input type="submit" value="Submit Review">
        </form>
        <p><a href="{{ url_for('index') }}">Back to Home</a></p>
    ''', product_id=product_id)

@app.route('/view_reviews')
def view_reviews():
    db = get_db()
    cursor = db.cursor()
    # Retrieve all reviews along with user and product details
    cursor.execute('''
        SELECT r.id, u.name as user_name, p.name as product_name, r.review_text, r.review_score
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        JOIN products p ON r.product_id = p.id
    ''')
    reviews = cursor.fetchall()
    return render_template_string('''
        <h1>All Reviews</h1>
        <ul>
        {% for review in reviews %}
            <li>
                <strong>{{ review['user_name'] }}</strong> reviewed 
                <strong>{{ review['product_name'] }}</strong>: 
                "{{ review['review_text'] }}" (Score: {{ review['review_score'] }})
            </li>
        {% endfor %}
        </ul>
        <p><a href="{{ url_for('index') }}">Back to Home</a></p>
    ''', reviews=reviews)

if __name__ == '__main__':
    with app.app_context():
        init_db()  # Initialize and populate the database on startup
    app.run(debug=True)
