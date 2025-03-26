import sqlite3
from sqlite3 import Error
from flask import Flask, request, render_template, redirect, url_for, session
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

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
    """Create a table for storing payment cards."""
    sql = '''
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        card_number TEXT,
        card_holder_name TEXT,
        expiration_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    '''
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS cards")
    cur.execute(sql)
    conn.commit()

@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    session['user_id'] = 12345

    if request.method == 'POST':
        card_number = request.form['card_number']
        cvv = request.form['cvv']
        expiration_date = request.form['expiration_date']
        card_holder_name = request.form['card_holder_name']
        billing_zip = request.form['billing_zip']

        # Input validation
        if not card_number or not cvv or not expiration_date or not card_holder_name or not billing_zip:
            # Handle missing fields (e.g., display an error message)
            return render_template('add_card.html', error_message="Please fill in all required fields.")

        try:
            expiration_date = datetime.datetime.strptime(request.form['expiration_date'], '%Y-%m')
        except ValueError:
            # Handle invalid date format
            return render_template('add_card.html', error_message="Invalid expiration date format.")

        if expiration_date < datetime.datetime.now():
            # Handle expired date
            return render_template('add_card.html', error_message="Expiration date cannot be in the past.")
        
        conn = create_connection('your_database.db')
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO cards (user_id, card_number, card_holder_name, expiration_date) VALUES (?, ?, ?, ?)",
                (session['user_id'], card_number, card_holder_name, expiration_date))
            conn.commit()

            return redirect(url_for('my_cards'))  # Assuming a route to display user's cards

    return render_template('add_card.html')

@app.route('/my-cards')
def my_cards():
    session['user_id'] = 12345
    conn = create_connection('your_database.db')
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards WHERE user_id = ?", (session['user_id'],))
        cards = cur.fetchall()
        cards = [dict(zip([col[0] for col in cur.description], row)) for row in cards]

                # Convert expiration_date to datetime
        for card in cards:
            card['expiration_date'] = datetime.datetime.strptime(card['expiration_date'], '%Y-%m-%d %H:%M:%S')    
            
    return render_template('my_cards.html', cards=cards)

@app.before_request
def create_tables_if_needed():
    if not hasattr(app, 'database_initialized'):
        conn = create_connection('your_database.db')
        with conn:
            create_table(conn)
        app.database_initialized = True

if __name__ == '__main__':
    app.run(debug=True)