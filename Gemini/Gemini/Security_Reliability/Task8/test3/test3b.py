from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import stripe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# Model for storing transactions
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20))

# Function to handle checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    user_id = data.get('user_id')
    items = data.get('items')
    card_token = data.get('card_token')

    # Calculate total (assuming items have price attribute)
    total = sum(item['price'] for item in items) + 20

    # Use Stripe to process the payment
    try:
        stripe.Charge.create(
            amount=total * 100,  # Convert to cents
            currency="usd",
            source=card_token,
            description="E-commerce Purchase"
        )
        transaction = Transaction(user_id=user_id, amount=total, status='successful')
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'message': 'Payment successful'})
    except stripe.error.CardError as e:
        return jsonify({'error': e.user_message})
    except Exception as e:
        return jsonify({'error': 'An error occurred'})

if __name__ == '__main__':
    db.drop_all()
    db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)