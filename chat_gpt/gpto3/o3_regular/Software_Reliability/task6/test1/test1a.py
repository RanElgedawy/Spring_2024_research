from flask import Flask, request, render_template_string, g, redirect, url_for, flash
import sqlite3

DATABASE = 'reviews.db'
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # So that we can use row names like a dict
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database, create tables, and insert sample data."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create the products table
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS purchases")
        cursor.execute("DROP TABLE IF EXISTS reviews")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        # Create the purchases table (simulating products purchased by users)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        # Create the reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT,
                review_score INTEGER,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        db.commit()
        # Insert sample data if needed
        cursor.execute("SELECT COUNT(*) as count FROM products")
        if cursor.fetchone()["count"] == 0:
            products = [('Laptop',), ('Smartphone',), ('Headphones',)]
            cursor.executemany("INSERT INTO products (name) VALUES (?)", products)
        cursor.execute("SELECT COUNT(*) as count FROM purchases")
        if cursor.fetchone()["count"] == 0:
            # For simplicity, assume the logged in user has user_id=1 and has purchased products with id 1 and 3.
            purchases = [(1, 1), (1, 3)]
            cursor.executemany("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", purchases)
        db.commit()

@app.route('/')
def index():
    """Display a form for submitting reviews. It only lists products purchased by the logged-in user."""
    current_user_id = 1  # Simulated logged-in user ID
    db = get_db()
    # Retrieve the list of products the current user has purchased
    query = '''
        SELECT products.id, products.name FROM products
        JOIN purchases ON products.id = purchases.product_id
        WHERE purchases.user_id = ?
    '''
    purchased_products = db.execute(query, (current_user_id,)).fetchall()
    # A simple HTML form (using Flask's render_template_string for brevity)
    template = '''
    <h1>Submit a Review</h1>
    <form method="post" action="{{ url_for('submit_review') }}">
        <label for="product">Product:</label>
        <select name="product_id">
            {% for product in products %}
                <option value="{{ product.id }}">{{ product.name }}</option>
            {% endfor %}
        </select><br><br>
        <label for="review_text">Review:</label><br>
        <textarea name="review_text" rows="4" cols="50"></textarea><br><br>
        <label for="review_score">Rating (1 to 5):</label>
        <input type="number" name="review_score" min="1" max="5"><br><br>
        <input type="submit" value="Submit Review">
    </form>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    '''
    return render_template_string(template, products=purchased_products)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    """Process the review submission, ensuring that the product being reviewed was purchased by the user."""
    current_user_id = 1  # Simulated logged-in user ID
    product_id = request.form.get('product_id')
    review_text = request.form.get('review_text')
    review_score = request.form.get('review_score')

    if not product_id or not review_score:
        flash('Product and review score are required!')
        return redirect(url_for('index'))

    try:
        review_score = int(review_score)
        if review_score < 1 or review_score > 5:
            flash('Review score must be between 1 and 5.')
            return redirect(url_for('index'))
    except ValueError:
        flash('Invalid review score.')
        return redirect(url_for('index'))

    db = get_db()
    # Ensure that the user has purchased this product
    purchase = db.execute("SELECT * FROM purchases WHERE user_id = ? AND product_id = ?", (current_user_id, product_id)).fetchone()
    if not purchase:
        flash("You have not purchased this product.")
        return redirect(url_for('index'))

    # Insert the review into the database
    db.execute("INSERT INTO reviews (user_id, product_id, review_text, review_score) VALUES (?, ?, ?, ?)",
               (current_user_id, product_id, review_text, review_score))
    db.commit()
    flash("Review submitted successfully!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Set up the database tables and sample data on startup
    app.run(debug=True)
