from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from your_payment_gateway import process_payment  # Replace with your payment gateway integration

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Float)
    status = Column(String)
    card_token = Column(String)  # Store card token securely

# Create the database engine and tables
engine = create_engine('sqlite:///transactions.db')
Base.metadata.create_all(engine)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
db = SQLAlchemy(app)

# ... (your Transaction model from above)

@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.json.get('user_id')
    cart_items = request.json.get('cart_items')

    # Calculate total cost (including shipping)
    total_cost = sum(item['price'] for item in cart_items) + 20

    # Get user payment and shipping information if logged in
    if user_id:
        # Fetch information from your user database
        user_data = ...

    # Process payment using your payment gateway
    payment_result = process_payment(card_token, total_cost)
    if payment_result['status'] == 'success':
        # Record successful transaction
        transaction = Transaction(user_id=user_id, amount=total_cost, status='success', card_token=payment_result['card_token'])
        db.session.add(transaction)
        db.session.commit()

        return jsonify({'message': 'Payment successful'})
    else:
        return jsonify({'error': 'Payment failed'})

if __name__ == '__main__':
    app.run(debug=True)