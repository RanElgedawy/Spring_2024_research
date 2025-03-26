import os
import sqlite3
import unittest
from flask import Flask, request, jsonify, g
import stripe

app = Flask(__name__)
app.config['DATABASE'] = 'ecommerce.db'
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY', 'sk_test_your_test_key')
app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_your_test_key')

# Initialize Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS transactions")
        db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount INTEGER,
                shipping_fee INTEGER,
                items TEXT,
                payment_intent_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def calculate_total(cart_items):
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    return subtotal + 2000  # $20 shipping fee in cents

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        data = request.get_json()
        user = data.get('user')  # Assume user is authenticated via session/JWT
        cart_items = data['cart']
        payment_method_id = data['payment_method_id']

        # Calculate total with shipping
        total = calculate_total(cart_items)

        # Create Stripe Payment Intent
        payment_intent = stripe.PaymentIntent.create(
            amount=total,
            currency='usd',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            metadata={
                'user_id': user['id'] if user else 'guest',
                'items': str([item['id'] for item in cart_items])
            }
        )

        if payment_intent.status == 'succeeded':
            # Record transaction
            db = get_db()
            db.execute('''
                INSERT INTO transactions 
                (user_id, total_amount, shipping_fee, items, payment_intent_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user['id'] if user else None,
                total - 2000,
                2000,
                str(cart_items),
                payment_intent.id
            ))
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Payment succeeded',
                'transaction_id': payment_intent.id
            }), 200

        return jsonify({'error': 'Payment failed'}), 400

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

class TestCheckout(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            init_db()
            db = get_db()
            db.execute('DELETE FROM transactions')

    def test_successful_checkout(self):
        # Mock Stripe payment method ID (use test card 4242 4242 4242 4242)
        mock_payload = {
            'user': {'id': 1},
            'cart': [{'id': 1, 'price': 5000, 'quantity': 2}],
            'payment_method_id': 'pm_card_visa'
        }
        
        response = self.app.post('/checkout', json=mock_payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('transaction_id', response.get_json())

if __name__ == '__main__':
    init_db()
    # Run tests with: python -m unittest filename.py
    # Start server with: flask run
    app.run(ssl_context='adhoc')  # HTTPS required for secure payments