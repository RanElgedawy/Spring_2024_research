import sqlite3
import flask
import html

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key

def create_review_table():
    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS reviews")
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            text TEXT,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/reviews/<int:product_id>', methods=['POST'])
def submit_review(product_id):
    user_id = flask.session['user_id']  # Assuming user is logged in
    text = flask.request.form['text']
    rating = int(flask.request.form['rating'])

    if not 1 <= rating <= 5:
        flask.flash('Invalid rating. Please choose a rating between 1 and 5.')
        return flask.redirect(flask.url_for('product_page', product_id=product_id))

    conn = sqlite3.connect('reviews.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO reviews (user_id, product_id, text, rating)
        VALUES (?, ?, ?, ?)
    ''', (user_id, product_id, html.escape(text), rating))
    conn.commit()
    conn.close()

    flask.flash('Review submitted successfully!')
    return flask.redirect(flask.url_for('product_page', product_id=product_id))

if __name__ == '__main__':
    create_review_table()
    app.run(debug=True)