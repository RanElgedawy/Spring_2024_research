import os
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuration - Use environment variables in production!
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Encryption setup
salt = os.urandom(16)
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=480000,
)
encryption_key = base64.urlsafe_b64encode(kdf.derive(app.config['SECRET_KEY'].encode()))
cipher_suite = Fernet(encryption_key)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add other user fields as needed

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    encrypted_number = db.Column(db.String(255), nullable=False)
    cardholder_name = db.Column(db.String(255), nullable=False)
    expiration_month = db.Column(db.Integer, nullable=False)
    expiration_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def decrypt_number(self):
        return cipher_suite.decrypt(self.encrypted_number.encode()).decode()

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Helper functions
def encrypt_card_data(card_number):
    return cipher_suite.encrypt(card_number.encode()).decode()

# Routes
@app.route('/api/payment-cards', methods=['POST'])
def add_payment_card():
    data = request.get_json()
    
    # Basic validation
    required_fields = ['card_number', 'cardholder_name', 'exp_month', 'exp_year', 'user_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Encrypt card number
        encrypted_number = encrypt_card_data(data['card_number'])

        # Create new payment card record
        new_card = PaymentCard(
            user_id=data['user_id'],
            encrypted_number=encrypted_number,
            cardholder_name=data['cardholder_name'],
            expiration_month=data['exp_month'],
            expiration_year=data['exp_year']
        )

        db.session.add(new_card)
        db.session.commit()

        return jsonify({
            'message': 'Card added successfully',
            'card_id': new_card.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Test route (remove in production)
@app.route('/test/add-card', methods=['POST'])
def test_add_card():
    test_data = {
        'card_number': '4242424242424242',
        'cardholder_name': 'Test User',
        'exp_month': 12,
        'exp_year': 2026,
        'user_id': 1
    }
    
    # Create test user if not exists
    if not User.query.get(1):
        db.session.add(User(id=1))
        db.session.commit()
    
    response = app.test_client().post('/api/payment-cards', json=test_data)
    return response

if __name__ == '__main__':
    app.run(debug=True)