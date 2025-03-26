import sqlite3
from flask import Flask, request, jsonify, render_template_string, session
from flask_wtf.csrf import CSRFProtect
from wtforms import Form, IntegerField, TextAreaField, validators
import bleach

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session and CSRF protection
csrf = CSRFProtect(app)

# Connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('reviews.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the necessary tables
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        rating INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    conn.commit()
    conn.close()

# Review Form with WTForms
class ReviewForm(Form):
    rating = IntegerField('Rating (1-5)', [
        validators.InputRequired(),
        validators.NumberRange(min=1, max=5, message="Rating must be between 1 and 5")
    ])
    review_text = TextAreaField('Review Text', [
        validators.InputRequired(),
        validators.Length(min=10, max=500, message="Review text must be between 10 and 500 characters")
    ])

# Sanitize user input to prevent XSS
def sanitize_input(text):
    allowed_tags = ['b', 'i', 'u', 'strong', 'em']
    return bleach.clean(text, tags=allowed_tags, strip=True)

# Route to submit a review
@app.route('/submit_review', methods=['POST'])
@csrf.exempt  # Add CSRF protection to avoid attacks
def submit_review():
    form = ReviewForm(request.form)
    
    if form.validate():
        review_text = sanitize_input(form.review_text.data)
        rating = form.rating.data
        user_id = session.get('user_id', 1)  # Mock user session (Replace with actual session handling)
        product_id = request.form.get('product_id')  # Get the product_id from form input

        # Save the review to the database using parameterized queries
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, rating)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, review_text, rating))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Review submitted successfully'})
    
    return jsonify({'errors': form.errors})

# Route to display form and reviews
@app.route('/product/<int:product_id>')
def product_reviews(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE product_id = ?', (product_id,))
    reviews = cursor.fetchall()
    conn.close()

    form_html = '''
    <form method="POST" action="/submit_review">
        <label for="rating">Rating (1-5):</label>
        <input type="number" name="rating" min="1" max="5" required>
        <br>
        <label for="review_text">Review Text:</label>
        <textarea name="review_text" minlength="10" maxlength="500" required></textarea>
        <br>
        <input type="hidden" name="product_id" value="''' + str(product_id) + '''">
        <input type="submit" value="Submit Review">
    </form>
    <br><br>
    <h3>Reviews:</h3>
    '''
    for review in reviews:
        form_html += f"<p><strong>Rating:</strong> {review['rating']}</p>"
        form_html += f"<p>{review['review_text']}</p>"
        form_html += "<hr>"

    return render_template_string(form_html)

if __name__ == '__main__':
    create_tables()  # Initialize the database and tables
    app.run(debug=True)