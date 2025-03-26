from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# Generate encryption key (store this securely in production!)
ENCRYPTION_KEY = hashlib.sha256(b'your-secure-passphrase').digest()

db = SQLAlchemy(app)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    encrypted_card = db.Column(db.String(512), nullable=False)
    iv = db.Column(db.String(128), nullable=False)
    expiration_month = db.Column(db.Integer, nullable=False)
    expiration_year = db.Column(db.Integer, nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    last_four_digits = db.Column(db.String(4), nullable=False)

    def __repr__(self):
        return f'<PaymentCard {self.last_four_digits}>'

def encrypt_card_data(card_number):
    # Generate random initialization vector
    iv = os.urandom(16)
    
    # Pad the data
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(card_number.encode()) + padder.finalize()
    
    # Encrypt
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    
    return base64.b64encode(encrypted_data).decode(), base64.b64encode(iv).decode()

def decrypt_card_data(encrypted_data, iv):
    encrypted_data = base64.b64decode(encrypted_data)
    iv = base64.b64decode(iv)
    
    # Decrypt
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Unpad
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded_data) + unpadder.finalize()).decode()

@app.route('/cards', methods=['POST'])
def add_card():
    data = request.json
    
    # Input validation
    required_fields = ['user_id', 'card_number', 'exp_month', 'exp_year', 'cardholder_name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Store only last four digits
    last_four = data['card_number'][-4:]
    
    # Encrypt card number
    encrypted_card, iv = encrypt_card_data(data['card_number'])
    
    new_card = PaymentCard(
        user_id=data['user_id'],
        encrypted_card=encrypted_card,
        iv=iv,
        expiration_month=data['exp_month'],
        expiration_year=data['exp_year'],
        cardholder_name=data['cardholder_name'],
        last_four_digits=last_four
    )
    
    db.session.add(new_card)
    db.session.commit()
    
    return jsonify({'message': 'Card added successfully', 'id': new_card.id}), 201

@app.route('/cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    cards = PaymentCard.query.filter_by(user_id=user_id).all()
    
    response = []
    for card in cards:
        response.append({
            'id': card.id,
            'last_four_digits': card.last_four_digits,
            'exp_month': card.expiration_month,
            'exp_year': card.expiration_year,
            'cardholder_name': card.cardholder_name
        })
    
    return jsonify(response), 200

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)