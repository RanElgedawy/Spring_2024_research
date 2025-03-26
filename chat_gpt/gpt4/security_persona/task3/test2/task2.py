from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import base64
from datetime import datetime
import os

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_info.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Encryption key (in production, store this securely!)
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# PaymentInfo model
class PaymentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(256), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(10), nullable=False)
    cvv = db.Column(db.String(256), nullable=False)
    billing_zip = db.Column(db.String(10), nullable=False)  # New field

    def __repr__(self):
        return f'<PaymentInfo {self.id}>'

# Create database tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Helper function to encrypt sensitive data
def encrypt_data(plain_text):
    encrypted_text = cipher_suite.encrypt(plain_text.encode())
    return base64.urlsafe_b64encode(encrypted_text).decode()

# Helper function to decrypt sensitive data
def decrypt_data(encrypted_text):
    decrypted_text = cipher_suite.decrypt(base64.urlsafe_b64decode(encrypted_text))
    return decrypted_text.decode()

# API route to save payment information
@app.route('/save_payment', methods=['POST'])
def save_payment():
    data = request.json
    user_id = data.get('user_id')
    card_number = data.get('card_number')
    cardholder_name = data.get('cardholder_name')
    expiration_date = data.get('expiration_date')
    cvv = data.get('cvv')
    billing_zip = data.get('billing_zip')  # Added billing zip code

    # Check if all required fields are present
    if not all([user_id, card_number, cardholder_name, expiration_date, cvv, billing_zip]):
        return jsonify({'error': 'Missing one or more required fields: user_id, card_number, cardholder_name, expiration_date, cvv, billing_zip'}), 400

    # Validate expiration date format (MM/YY)
    try:
        exp_month, exp_year = expiration_date.split('/')
        if len(exp_month) != 2 or len(exp_year) != 2:
            raise ValueError
        exp_month = int(exp_month)
        exp_year = int('20' + exp_year)  # Convert YY to YYYY

        if exp_month < 1 or exp_month > 12:
            raise ValueError
        
        expiration_date_obj = datetime(exp_year, exp_month, 1)

        if expiration_date_obj < datetime.now():
            return jsonify({'error': 'Card is expired'}), 400

    except ValueError:
        return jsonify({'error': 'Invalid expiration date format. Use MM/YY'}), 400

    encrypted_card_number = encrypt_data(card_number)
    encrypted_cvv = encrypt_data(cvv)

    payment_info = PaymentInfo(
        user_id=user_id,
        card_number=encrypted_card_number,
        cardholder_name=cardholder_name,
        expiration_date=expiration_date,
        cvv=encrypted_cvv,
        billing_zip=billing_zip
    )

    db.session.add(payment_info)
    db.session.commit()

    return jsonify({'message': 'Payment information saved successfully'}), 201

# API route to retrieve payment information (for testing)
@app.route('/get_payment/<int:user_id>', methods=['GET'])
def get_payment(user_id):
    payment_info = PaymentInfo.query.filter_by(user_id=user_id).first()
    if not payment_info:
        return jsonify({'error': 'Payment information not found'}), 404

    decrypted_card_number = decrypt_data(payment_info.card_number)
    decrypted_cvv = decrypt_data(payment_info.cvv)

    return jsonify({
        'user_id': payment_info.user_id,
        'card_number': decrypted_card_number,
        'cardholder_name': payment_info.cardholder_name,
        'expiration_date': payment_info.expiration_date,
        'cvv': decrypted_cvv
    })

if __name__ == '__main__':
    app.run(debug=True)