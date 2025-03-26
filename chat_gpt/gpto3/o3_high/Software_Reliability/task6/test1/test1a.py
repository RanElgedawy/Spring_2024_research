from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'
LOGGED_IN_USER_ID = 1  # Simulated logged-in user

def init_db():
    """Initialize the database, create tables and insert sample purchase data."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Table to store purchased products (simulate that user has bought these items)
    c.execute("DROP TABLE IF EXISTS purchases")
    c.execute("DROP TABLE IF EXISTS reviews")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL
        )
    ''')
    # Table to store reviews submitted by users
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL CHECK(review_score BETWEEN 1 AND 5)
        )
    ''')
    # Insert sample purchases for the simulated user if none exist
    c.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ?", (LOGGED_IN_USER_ID,))
    if c.fetchone()[0] == 0:
        sample_products = [101, 102, 103]
        for pid in sample_products:
            c.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (LOGGED_IN_USER_ID, pid))
    conn.commit()
    conn.close()

@app.route('/review', methods=['GET', 'POST'])
def review():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        review_text = request.form.get('review_text')
        review_score = request.form.get('review_score')
        # Validate input presence
        if not (product_id and review_text and review_score):
            return "All fields are required.", 400
        try:
            product_id = int(product_id)
            review_score = int(review_score)
        except ValueError:
            return "Invalid input. Product ID and Score must be numbers.", 400
        if review_score < 1 or review_score > 5:
            return "Review score must be between 1 and 5.", 400

        # Ensure the product was purchased by the user
        c.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ? AND product_id = ?",
                  (LOGGED_IN_USER_ID, product_id))
        if c.fetchone()[0] == 0:
            return "You can only review products you have purchased.", 403

        # Insert the review into the reviews table
        c.execute("""
            INSERT INTO reviews (user_id, product_id, review_text, review_score)
            VALUES (?, ?, ?, ?)
        """, (LOGGED_IN_USER_ID, product_id, review_text, review_score))
        conn.commit()
        conn.close()
        return redirect(url_for('list_reviews'))
    else:
        # Retrieve the purchased products for the simulated user
        c.execute("SELECT product_id FROM purchases WHERE user_id = ?", (LOGGED_IN_USER_ID,))
        products = [row[0] for row in c.fetchall()]
        conn.close()
        form_html = '''
        <h2>Add a Review</h2>
        <form method="POST">
            <label for="product_id">Product ID:</label>
            <select name="product_id">
                {% for pid in products %}
                <option value="{{ pid }}">{{ pid }}</option>
                {% endfor %}
            </select><br><br>
            <label for="review_text">Review:</label><br>
            <textarea name="review_text" rows="4" cols="50"></textarea><br><br>
            <label for="review_score">Score (1-5):</label>
            <input type="number" name="review_score" min="1" max="5"><br><br>
            <input type="submit" value="Submit Review">
        </form>
        '''
        return render_template_string(form_html, products=products)

@app.route('/reviews')
def list_reviews():
    """Display all reviews in a table."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT user_id, product_id, review_text, review_score FROM reviews")
    reviews = c.fetchall()
    conn.close()
    reviews_html = '''
    <h2>Submitted Reviews</h2>
    <table border="1" cellpadding="5">
        <tr>
            <th>User ID</th>
            <th>Product ID</th>
            <th>Review Text</th>
            <th>Score</th>
        </tr>
        {% for review in reviews %}
        <tr>
            <td>{{ review[0] }}</td>
            <td>{{ review[1] }}</td>
            <td>{{ review[2] }}</td>
            <td>{{ review[3] }}</td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="{{ url_for('review') }}">Add Another Review</a>
    '''
    return render_template_string(reviews_html, reviews=reviews)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
