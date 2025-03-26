from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

def create_connection(db_file):
    """Create a database connection."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn):
    """Create a table for storing reviews."""
    sql = """ CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                text_review TEXT,
                review_score INTEGER
            ); """
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS reviews")
    cur.execute(sql)
    conn.commit()

@app.route('/add_review/<int:product_id>', methods=['GET', 'POST'])
def add_review(product_id):
    if request.method == 'POST':
        user_id = 1  # Replace with actual user ID
        text_review = request.form['text_review']
        review_score = int(request.form['review_score'])

        conn = create_connection('reviews.db')
        create_table(conn)

        sql = """ INSERT INTO reviews (user_id, product_id, text_review, review_score)
                  VALUES (?, ?, ?, ?) """
        cur = conn.cursor()
        cur.execute(sql, (user_id, product_id, text_review, review_score))
        conn.commit()
        conn.close()

        return redirect(url_for('product_page', product_id=product_id))

    return render_template('add_review.html', product_id=product_id)

# ... Other routes and views ...

if __name__ == '__main__':
    app.run(debug=True)