from flask import Flask, request, jsonify, render_template, redirect, url_for
import stripe
import sqlite3

app = Flask(__name__)

# Replace with your Stripe API key
stripe.api_key = "your_stripe_api_key"

# Connect to the database
conn = sqlite3.connect('transactions.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS transactions")

# Create the transactions table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
conn.commit()

@app.route('/checkout', methods=['POST'])
def checkout():
    # Retrieve user information if logged in
    user_id = None  # Replace with actual user ID retrieval logic
    payment_info = None  # Replace with actual payment info retrieval

    # Calculate total with shipping fee
    total = get_cart_total() + 20

    # Create a Stripe charge
    try:
        charge = stripe.Charge.create(
            amount=total * 100,  # Convert to cents
            currency='usd',
            source=request.form['stripeToken'],
            description='E-commerce Purchase'
        )
    except stripe.error.CardError as e:
        # Handle card errors
        return jsonify({'error': e.user_message})

    # Record successful transaction
    c.execute("INSERT INTO transactions (user_id, amount, status) VALUES (?, ?, ?)",
              (user_id, total, "successful"))
    conn.commit()

    # Redirect to a success page or send a confirmation email
    return jsonify({'success': True})

# Helper function to get the total from the cart
def get_cart_total():
    # Implement logic to calculate the total based on items in the cart
    return 100  # Example total

if __name__ == '__main__':
    app.run(debug=True)