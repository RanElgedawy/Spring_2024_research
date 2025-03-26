from flask import Flask, request, session, render_template_string, redirect, url_for, g, flash
import sqlite3, secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
DATABASE = 'reviews.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create the reviews table
        cursor.execute("DROP TABLE IF EXISTS reviews")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS purchases")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create a users table to store user information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL
            )
        ''')
        # Create a purchases table to record which user bought which product
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Insert a dummy user (if not already present)
        cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'testuser')")
        # Insert a dummy purchase: user 1 bought product 1
        cursor.execute("INSERT OR IGNORE INTO purchases (user_id, product_id) VALUES (1, 1)")
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

def verify_csrf_token(token):
    stored_token = session.pop('csrf_token', None)
    return stored_token and stored_token == token

# For demonstration purposes, simulate a logged-in user.
@app.before_request
def simulate_login():
    session.setdefault('user_id', 1)

@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def review(product_id):
    db = get_db()
    cursor = db.cursor()

    # Ensure the user exists.
    user_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        flash("User does not exist. Please log in.")
        return redirect(url_for('review', product_id=product_id))

    # Verify that the user has purchased the product.
    cursor.execute("SELECT * FROM purchases WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    purchase = cursor.fetchone()
    if not purchase:
        flash("You have not purchased this product and cannot leave a review.")
        return redirect(url_for('review', product_id=product_id))

    if request.method == 'POST':
        # CSRF protection check.
        token = request.form.get('csrf_token', '')
        if not verify_csrf_token(token):
            return "Invalid CSRF token", 400

        rating = request.form.get('rating', type=int)
        text = request.form.get('text', '')
        if not rating or rating < 1 or rating > 5:
            flash("Rating must be a number between 1 and 5.")
            return redirect(url_for('review', product_id=product_id))
        if not text.strip():
            flash("Review text cannot be empty.")
            return redirect(url_for('review', product_id=product_id))

        # Use parameterized queries to safely insert the review.
        cursor.execute(
            'INSERT INTO reviews (product_id, user_id, rating, text) VALUES (?, ?, ?, ?)',
            (product_id, user_id, rating, text)
        )
        db.commit()
        flash("Review submitted successfully.")
        return redirect(url_for('review', product_id=product_id))

    # Generate a new CSRF token for the form.
    csrf_token = generate_csrf_token()
    cursor.execute('''
        SELECT * FROM reviews
        WHERE product_id = ?
        ORDER BY created_at DESC
    ''', (product_id,))
    reviews = cursor.fetchall()
    return render_template_string('''
        <!doctype html>
        <html>
        <head>
            <title>Product Review</title>
        </head>
        <body>
            <h1>Leave a Review for Product {{ product_id }}</h1>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <ul style="color:red;">
                {% for message in messages %}
                  <li>{{ message }}</li>
                {% endfor %}
                </ul>
              {% endif %}
            {% endwith %}
            <form method="POST">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <label for="rating">Rating (1-5):</label>
                <input type="number" id="rating" name="rating" min="1" max="5" required><br><br>
                <label for="text">Review:</label><br>
                <textarea id="text" name="text" rows="4" cols="50" required></textarea><br><br>
                <input type="submit" value="Submit Review">
            </form>
            <h2>Existing Reviews</h2>
            {% if reviews %}
                {% for review in reviews %}
                    <div style="border:1px solid #ccc; margin:10px; padding:10px;">
                        <strong>User ID:</strong> {{ review.user_id }} <br>
                        <strong>Rating:</strong> {{ review.rating }}<br>
                        <strong>Review:</strong> {{ review.text|e }}<br>
                        <em>Submitted on {{ review.created_at }}</em>
                    </div>
                {% endfor %}
            {% else %}
                <p>No reviews yet.</p>
            {% endif %}
        </body>
        </html>
    ''', product_id=product_id, csrf_token=csrf_token, reviews=reviews)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
