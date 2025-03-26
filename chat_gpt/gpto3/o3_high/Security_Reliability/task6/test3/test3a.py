import sqlite3
import secrets
from flask import Flask, request, session, redirect, url_for, render_template_string, flash

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'  # Replace with a strong secret key in production

DATABASE = 'reviews.db'

def init_db():
    """Initialize the SQLite database and create the reviews table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database automatically on startup.
init_db()

# HTML template embedded as a string.
template = '''
<!doctype html>
<html>
<head>
    <title>Product Reviews</title>
</head>
<body>
    <h1>Leave a Review</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="POST" action="{{ url_for('index') }}">
        <label for="product_id">Product ID:</label><br>
        <input type="number" id="product_id" name="product_id" required><br><br>

        <label for="rating">Rating (1 to 5):</label><br>
        <input type="number" id="rating" name="rating" min="1" max="5" required><br><br>

        <label for="review_text">Review:</label><br>
        <textarea id="review_text" name="review_text" rows="4" cols="50" required></textarea><br><br>

        <!-- CSRF token to prevent cross-site request forgery -->
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="submit" value="Submit Review">
    </form>

    <h2>Existing Reviews</h2>
    {% if reviews %}
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>ID</th>
            <th>Product ID</th>
            <th>Rating</th>
            <th>Review</th>
            <th>Created At</th>
        </tr>
        {% for review in reviews %}
        <tr>
            <td>{{ review[0] }}</td>
            <td>{{ review[1] }}</td>
            <td>{{ review[2] }}</td>
            <td>{{ review[3] }}</td>
            <td>{{ review[4] }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No reviews yet.</p>
    {% endif %}
</body>
</html>
'''

def get_reviews():
    """Retrieve all reviews from the database, ordered by most recent."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_id, rating, review_text, created_at FROM reviews ORDER BY created_at DESC")
    reviews = cursor.fetchall()
    conn.close()
    return reviews

@app.before_request
def set_csrf_token():
    """Ensure a CSRF token is available in the session for each request."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # CSRF protection: verify token from form matches the one in the session.
        form_csrf_token = request.form.get('csrf_token')
        if not form_csrf_token or form_csrf_token != session.get('csrf_token'):
            flash('Invalid CSRF token')
            return redirect(url_for('index'))
        try:
            # Retrieve and validate form data
            product_id = int(request.form.get('product_id'))
            rating = int(request.form.get('rating'))
            review_text = request.form.get('review_text')
        except (ValueError, TypeError):
            flash('Invalid input data.')
            return redirect(url_for('index'))

        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5.')
            return redirect(url_for('index'))

        # Prevent SQL injection by using parameterized queries
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reviews (product_id, rating, review_text) VALUES (?, ?, ?)",
                       (product_id, rating, review_text))
        conn.commit()
        conn.close()

        flash('Review submitted successfully.')
        return redirect(url_for('index'))

    # On GET requests, retrieve and display existing reviews.
    reviews = get_reviews()
    return render_template_string(template, csrf_token=session.get('csrf_token'), reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
