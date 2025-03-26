from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet
import base64
import os
from datetime import datetime

# Flask application setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Generate a key for encryption/decryption
# WARNING: In a real-world application, store this key securely!
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# User model (assuming the user is already registered)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# PaymentCard model to store encrypted card information
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.LargeBinary, nullable=False)
    card_holder = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(7), nullable=False)  # Format: MM/YYYY
    cvv = db.Column(db.LargeBinary, nullable=False)
    billing_zip = db.Column(db.String(10), nullable=False)
    user = db.relationship('User', backref=db.backref('cards', lazy=True))

# Ensure that tables are created within the application context
with app.app_context():
    db.drop_all()
    db.create_all()

# Route to register a new payment card
@app.route('/register_card', methods=['POST'])
def register_card():
    try:
        # Extract parameters from the request
        user_id = request.json.get('user_id')
        card_number = request.json.get('card_number')
        card_holder = request.json.get('card_holder')
        expiration_date = request.json.get('expiration_date')
        cvv = request.json.get('cvv')
        billing_zip = request.json.get('billing_zip')

        # Validate that all required parameters are present
        if not user_id:
            return jsonify({'message': 'User ID is required!'}), 400
        if not card_number:
            return jsonify({'message': 'Card number is required!'}), 400
        if not card_holder:
            return jsonify({'message': 'Name on card is required!'}), 400
        if not expiration_date:
            return jsonify({'message': 'Expiration date is required!'}), 400
        if not cvv:
            return jsonify({'message': 'CVV is required!'}), 400
        if not billing_zip:
            return jsonify({'message': 'Billing zip code is required!'}), 400

        # Validate the expiration date format and that it is not in the past
        try:
            exp_date = datetime.strptime(expiration_date, "%m/%Y")
            if exp_date < datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0):
                return jsonify({'message': 'Expiration date cannot be in the past!'}), 400
        except ValueError:
            return jsonify({'message': 'Expiration date must be in MM/YYYY format!'}), 400

        # Encrypt the sensitive information
        encrypted_card_number = cipher_suite.encrypt(card_number.encode())
        encrypted_cvv = cipher_suite.encrypt(cvv.encode())

        # Create a new PaymentCard entry
        new_card = PaymentCard(
            user_id=user_id,
            card_number=encrypted_card_number,
            card_holder=card_holder,
            expiration_date=expiration_date,
            cvv=encrypted_cvv,
            billing_zip=billing_zip
        )
        db.session.add(new_card)
        db.session.commit()

        return jsonify({'message': 'Card registered successfully!'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'User does not exist or card registration failed!'}), 400

    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

# Route to retrieve stored cards for a user (for testing purposes)
@app.route('/get_cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found!'}), 404

        cards = []
        for card in user.cards:
            decrypted_card_number = cipher_suite.decrypt(card.card_number).decode()
            decrypted_cvv = cipher_suite.decrypt(card.cvv).decode()
            cards.append({
                'card_holder': card.card_holder,
                'card_number': decrypted_card_number,
                'expiration_date': card.expiration_date,
                'cvv': decrypted_cvv,
                'billing_zip': card.billing_zip
            })

        return jsonify({'cards': cards}), 200

    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    # You should use 'flask run' command in production
    app.run(debug=True)