from flask import Flask, request, session, g, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import stripe
import os
import logging

# Configuration
DATABASE = '/tmp/ecommerce.db'
SECRET_KEY = os.urandom(24)
STRIPE_API_KEY = 'sk_test_...'  # Use test key from Stripe Dashboard
STRIPE_ENDPOINT_SECRET = 'whsec_...'  # Webhook secret

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
stripe.api_key = STRIPE_API_KEY

# Database Models
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    stripe_payment_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Helper Functions
def calculate_total(cart_items):
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    return subtotal + 20  # Add $20 shipping

# Checkout Process
@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        # Authentication check
        if 'user_id' not in session:
            return {'error': 'Authentication required'}, 401

        # Get user and cart data (mock implementation - replace with actual DB queries)
        user_id = session['user_id']
        cart_items = get_user_cart(user_id)  # Implement this function
        total_amount = calculate_total(cart_items)

        # Create Stripe PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Convert to cents
            currency='usd',
            payment_method_types=['card'],
            metadata={
                'user_id': user_id,
                'cart_items': str(len(cart_items))
            }
        )

        return {'clientSecret': payment_intent.client_secret}

    except Exception as e:
        logging.error(f"Checkout error: {str(e)}")
        return {'error': 'Checkout failed'}, 500

# Webhook for payment confirmation
@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Record successful transaction
        transaction = Transaction(
            user_id=payment_intent.metadata.user_id,
            amount=payment_intent.amount / 100,
            currency=payment_intent.currency,
            stripe_payment_id=payment_intent.id,
            status='completed'
        )
        db.session.add(transaction)
        db.session.commit()

    return '', 200

# Test Implementation
@app.route('/test-checkout', methods=['GET', 'POST'])
def test_checkout():
    if request.method == 'POST':
        # Simulate logged-in user
        session['user_id'] = 1
        
        # Simulate cart items
        mock_cart = [
            {'product_id': 1, 'price': 50.00, 'quantity': 2},
            {'product_id': 2, 'price': 30.00, 'quantity': 1}
        ]
        
        total = calculate_total(mock_cart)
        return f'''
            <h2>Test Checkout (Total: ${total:.2f})</h2>
            <form id="payment-form">
                <div id="card-element"></div>
                <button id="submit">Pay</button>
            </form>
            <script src="https://js.stripe.com/v3/"></script>
            <script>
                const stripe = Stripe('pk_test_...');
                // Add Stripe Elements here
            </script>
        '''
    return redirect(url_for('checkout'))

# Database Initialization
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    # app.run(ssl_context='adhoc')  # HTTPS required for production