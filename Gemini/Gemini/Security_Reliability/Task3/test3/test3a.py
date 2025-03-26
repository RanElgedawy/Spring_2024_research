import stripe
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Replace with your Stripe API key
stripe.api_key = "your_stripe_api_key"

# Create a database table to store tokenized card details
# (Assuming you're using SQLite)
import sqlite3
conn = sqlite3.connect('your_database.db')
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS cards")
c.execute('''CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY, user_id INTEGER, token TEXT)''')
conn.commit()

@app.route('/add-card', methods=['POST'])
def add_card():
    try:
        token = request.json['token']
        user_id = 1  # Replace with the actual user ID

        # Create a Stripe Customer to store the token
        customer = stripe.Customer.create(
            source=token
        )

        # Store the customer ID and token in your database
        c.execute("INSERT INTO cards (user_id, token) VALUES (?, ?)", (user_id, customer.id))
        conn.commit()

        return jsonify({'message': 'Card added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

# ... other routes and functions ...

if __name__ == '__main__':
    app.run()