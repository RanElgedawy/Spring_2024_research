from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# Add a new payment card
@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        user_id = 1  # Replace with actual user ID
        card_number = request.form['card_number']
        card_holder_name = request.form['card_holder_name']
        expiration_date = request.form['expiration_date']
        cvv = request.form['cvv']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO payment_cards (user_id, card_number, card_holder_name, expiration_date, cvv) VALUES (?, ?, ?, ?, ?)",
                    (user_id, card_number, card_holder_name, expiration_date, cvv))
        conn.commit()
        conn.close()

        return redirect(url_for('payment_methods'))  # Redirect to a payment methods page

    return render_template('add_card_a.html')

if __name__ == '__main__':
    app.run(debug=True)