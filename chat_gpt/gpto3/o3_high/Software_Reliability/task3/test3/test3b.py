from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
# Using SQLite for demonstration. In production, switch to your preferred DB.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model for PaymentCard. Note: In a real-world app, you should not store sensitive data like CVV.
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # In a real app, this would be a foreign key
    card_number = db.Column(db.String(20), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.String(10), nullable=False)  # Format: MM/YY
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Automatically create tables before the first request.
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

# Endpoint to add a new payment card.
# Expected JSON body: { "user_id": <int>, "card_number": <str>, "cardholder_name": <str>, "expiry_date": <str> }
@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['user_id', 'card_number', 'cardholder_name', 'expiry_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    # In a real application, add further validations (e.g., Luhn check on card number)
    new_card = PaymentCard(
        user_id=data['user_id'],
        card_number=data['card_number'],
        cardholder_name=data['cardholder_name'],
        expiry_date=data['expiry_date']
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Payment card added successfully', 'card_id': new_card.id}), 201

# Endpoint to list payment cards for a specific user.
# This is provided for testing purposes.
@app.route('/list_cards', methods=['GET'])
def list_cards():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id query parameter'}), 400

    cards = PaymentCard.query.filter_by(user_id=user_id).all()
    result = []
    for card in cards:
        result.append({
            'id': card.id,
            'card_number': card.card_number,
            'cardholder_name': card.cardholder_name,
            'expiry_date': card.expiry_date,
            'created_at': card.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)
