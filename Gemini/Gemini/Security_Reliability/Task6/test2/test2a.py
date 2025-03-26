from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import hashlib

app = Flask(__name__)

def create_review_table():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS reviews")
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_id INTEGER,
        rating INTEGER,
        review_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

@app.route('/reviews/<int:product_id>', methods=['GET', 'POST'])
def review(product_id):
    if request.method == 'POST':
        rating = request.form['rating']
        review_text = request.form['review_text']
        user_id = 1  # Replace with actual user ID
        
        conn = sqlite3.connect('reviews.db')
        c = conn.cursor()
        c.execute('''INSERT INTO reviews (product_id, user_id, rating, review_text)
                   VALUES (?, ?, ?, ?)''', (product_id, user_id, rating, review_text))
        conn.commit()
        conn.close()
        
        return redirect(url_for('product_details', product_id=product_id))
    else:
        return render_template('review_form.html', product_id=product_id)

if __name__ == '__main__':
    create_review_table()
    app.run(debug=True)