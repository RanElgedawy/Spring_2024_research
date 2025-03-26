# app.py
from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import os
import re
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Generate encryption key if not exists (In production, use a proper key management system)
encryption_key = os.environ.get('ENCRYPTION_KEY')
if not encryption_key:
    encryption_key = Fernet.generate_key().decode()
    print(f'Generated encryption key: {encryption_key} - Store this securely!')
    
cipher_suite = Fernet(encryption_key.encode())

db = SQLAlchemy(app)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    encrypted_number = db.Column(db.LargeBinary, nullable=False)
    last_four = db.Column(db.String(4), nullable=False)
    expiration_month = db.Column(db.Integer, nullable=False)
    expiration_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def decrypt_number(self):
        return cipher_suite.decrypt(self.encrypted_number).decode()

@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

def validate_card(card_number, expiration_month, expiration_year):
    # Basic validation
    if not re.match(r'^\d{13,19}$', card_number):
        return False, 'Invalid card number format'
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if (expiration_year < current_year) or \
       (expiration_year == current_year and expiration_month < current_month):
        return False, 'Card has expired'
    
    return True, ''

@app.route('/add-card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
        
    data = request.get_json()
    
    # Validate input
    required_fields = ['cardholder_name', 'card_number', 'expiration_month', 'expiration_year']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Basic validation
    is_valid, message = validate_card(
        data['card_number'],
        data['expiration_month'],
        data['expiration_year']
    )
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Encrypt card number
    try:
        encrypted_number = cipher_suite.encrypt(data['card_number'].encode())
    except Exception as e:
        return jsonify({'error': 'Encryption failed'}), 500
    
    # Store payment card
    new_card = PaymentCard(
        user_id=session['user_id'],
        cardholder_name=data['cardholder_name'],
        encrypted_number=encrypted_number,
        last_four=data['card_number'][-4:],
        expiration_month=data['expiration_month'],
        expiration_year=data['expiration_year']
    )
    
    try:
        db.session.add(new_card)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500
    
    return jsonify({'message': 'Card added successfully', 'last_four': new_card.last_four})

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # Always use HTTPS in production