from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('reviews.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_review/<int:product_id>', methods=['GET', 'POST'])
def add_review(product_id):
    conn = get_db_connection()
    user_id = 1  # Replace with actual user ID from authentication

    if request.method == 'POST':
        review_text = request.form['review_text']
        rating = int(request.form['rating'])

        conn.execute(
            'INSERT INTO reviews (user_id, product_id, review, rating) VALUES (?, ?, ?, ?)',
            (user_id, product_id, review_text, rating)
        )
        conn.commit()
        return redirect(url_for('product_page', product_id=product_id))

    return render_template('add_review.html', product_id=product_id)

# ... other routes and views in your Flask application

if __name__ == '__main__':
    app.run(debug=True)