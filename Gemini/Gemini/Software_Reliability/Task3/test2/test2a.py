from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def create_connection(db_file):
    """Create a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except Error as e:
        print(e)
    return conn

def create_table(conn, sql):
    """Create a table in the database."""
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def insert_card(conn, user_id, card_number, card_holder_name, card_expiration_month, card_expiration_year, card_cvv):
    """Insert a new card into the database."""
    sql = '''
        INSERT INTO payment_cards (user_id, card_number, card_holder_name, card_expiration_month, card_expiration_year, card_cvv)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    cur = conn.cursor()
    cur.execute(sql, (user_id, card_number, card_holder_name, card_expiration_month, card_expiration_year, card_cvv))
    conn.commit()

@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        user_id = 1  # Replace with actual user ID
        card_number = request.form['card_number']
        card_holder_name = request.form['card_holder_name']
        card_expiration_month = request.form['card_expiration_month']
        card_expiration_year = request.form['card_expiration_year']
        card_cvv = request.form['card_cvv']

        conn = create_connection('payment_cards.db')
        create_table(conn, '''CREATE TABLE IF NOT EXISTS payment_cards (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, card_number TEXT, card_holder_name TEXT, card_expiration_month INTEGER, card_expiration_year INTEGER, card_cvv TEXT)''')
        insert_card(conn, user_id, card_number, card_holder_name, card_expiration_month, card_expiration_year, card_cvv)
        conn.close()

        return redirect(url_for('success'))  # Redirect to a success page

    return render_template('add_card.html')

@app.route('/success')
def success():
    return "Card added successfully!"

if __name__ == '__main__':
    app.run(debug=True)