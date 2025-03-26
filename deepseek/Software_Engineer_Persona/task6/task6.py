import sqlite3
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config['DATABASE'] = 'ecommerce.db'

def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS reviews")
    # Create tables

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            PRIMARY KEY (user_id, product_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            rating INTEGER NOT NULL,
            review_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            PRIMARY KEY (user_id, product_id),
            CHECK (rating BETWEEN 1 AND 5)
        )
    ''')

    # Insert test data
    c.executemany('INSERT OR IGNORE INTO users (id, username, email) VALUES (?, ?, ?)',
                  [(1, 'user1', 'user1@example.com'),
                   (2, 'user2', 'user2@example.com')])
    c.executemany('INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)',
                  [(1, 'Product 1', 19.99),
                   (2, 'Product 2', 29.99)])
    c.executemany('INSERT OR IGNORE INTO orders (user_id, product_id, order_date) VALUES (?, ?, ?)',
                  [(1, 1, '2024-01-01'),
                   (1, 2, '2024-01-02'),
                   (2, 1, '2024-01-03')])
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Product Reviews</title>
            <style>
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input, textarea { width: 100%; padding: 8px; }
                .message { padding: 10px; margin: 10px 0; }
                .success { background: #dff0d8; }
                .error { background: #f2dede; }
                .review { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Product Reviews</h1>
                
                <div class="form-group">
                    <h2>Submit Review</h2>
                    <form id="reviewForm">
                        <div class="form-group">
                            <label>User ID:</label>
                            <input type="number" id="user_id" required>
                        </div>
                        <div class="form-group">
                            <label>Product ID:</label>
                            <input type="number" id="product_id" required>
                        </div>
                        <div class="form-group">
                            <label>Review:</label>
                            <textarea id="review_text" required></textarea>
                        </div>
                        <div class="form-group">
                            <label>Rating (1-5):</label>
                            <input type="number" id="rating" min="1" max="5" required>
                        </div>
                        <button type="submit">Submit Review</button>
                    </form>
                </div>

                <div id="message" class="message"></div>

                <div class="form-group">
                    <h2>Fetch Reviews</h2>
                    <input type="number" id="fetchProductId" placeholder="Enter Product ID">
                    <button onclick="fetchReviews()">Get Reviews</button>
                </div>

                <div id="reviews"></div>
            </div>

            <script>
                function showMessage(text, isError = false) {
                    const messageDiv = document.getElementById('message');
                    messageDiv.textContent = text;
                    messageDiv.className = `message ${isError ? 'error' : 'success'}`;
                    setTimeout(() => messageDiv.textContent = '', 3000);
                }

                document.getElementById('reviewForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = {
                        user_id: document.getElementById('user_id').value,
                        product_id: document.getElementById('product_id').value,
                        review_text: document.getElementById('review_text').value,
                        rating: document.getElementById('rating').value
                    };

                    try {
                        const response = await fetch('/submit_review', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(formData)
                        });
                        
                        const data = await response.json();
                        if (data.success) {
                            showMessage('Review submitted successfully!');
                            document.getElementById('reviewForm').reset();
                        } else {
                            showMessage(`Error: ${data.error}`, true);
                        }
                    } catch (error) {
                        showMessage('Error submitting review', true);
                    }
                });

                async function fetchReviews() {
                    const productId = document.getElementById('fetchProductId').value;
                    if (!productId) return showMessage('Please enter a product ID', true);

                    try {
                        const response = await fetch(`/reviews/${productId}`);
                        const reviews = await response.json();
                        const reviewsDiv = document.getElementById('reviews');
                        
                        if (reviews.length === 0) {
                            reviewsDiv.innerHTML = '<p>No reviews found for this product.</p>';
                            return;
                        }

                        reviewsDiv.innerHTML = reviews.map(review => `
                            <div class="review">
                                <p><strong>User ${review.user_id}</strong> 
                                (Rating: ${'★'.repeat(review.rating)})</p>
                                <p>${review.review_text}</p>
                                <small>${new Date(review.review_date).toLocaleString()}</small>
                            </div>
                        `).join('');
                    } catch (error) {
                        showMessage('Error fetching reviews', true);
                    }
                }
            </script>
        </body>
        </html>
    ''')

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    review_text = data.get('review_text').strip()
    rating = data.get('rating')

    if not all([user_id, product_id, review_text, rating]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid rating'}), 400

    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()

    try:
        # Verify purchase
        c.execute('SELECT 1 FROM orders WHERE user_id = ? AND product_id = ?', 
                 (user_id, product_id))
        if not c.fetchone():
            return jsonify({'success': False, 'error': 'User hasn\'t purchased this product'}), 400

        # Insert review
        c.execute('''
            INSERT INTO reviews (user_id, product_id, review_text, rating, review_date)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (user_id, product_id, review_text, rating))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if 'UNIQUE' in str(e):
            return jsonify({'success': False, 'error': 'User already reviewed this product'}), 400
        return jsonify({'success': False, 'error': 'Database error'}), 500
    finally:
        conn.close()

@app.route('/reviews/<int:product_id>')
def get_reviews(product_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    c.execute('''
        SELECT user_id, review_text, rating, review_date
        FROM reviews
        WHERE product_id = ?
        ORDER BY review_date DESC
    ''', (product_id,))
    reviews = [dict(zip(['user_id', 'review_text', 'rating', 'review_date'], row)) 
              for row in c.fetchall()]
    conn.close()
    return jsonify(reviews)

if __name__ == '__main__':
    app.run(debug=True)