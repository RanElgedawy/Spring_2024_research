from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Encryption configuration
ENCRYPTION_KEY = base64.urlsafe_b64decode(os.environ['ENCRYPTION_KEY'])

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    encrypted_card = db.Column(db.LargeBinary, nullable=False)
    iv = db.Column(db.LargeBinary, nullable=False)
    expiration_month = db.Column(db.Integer, nullable=False)
    expiration_year = db.Column(db.Integer, nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)

def encrypt_card(card_number):
    iv = secrets.token_bytes(12)
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(card_number.encode()) + padder.finalize()
    
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return iv, encrypted + encryptor.tag

def decrypt_card(iv, encrypted_data):
    tag = encrypted_data[-16:]
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded = decryptor.update(encrypted_data[:-16]) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode()

@app.route('/cards', methods=['POST'])
def add_card():
    data = request.get_json()
    
    try:
        iv, encrypted = encrypt_card(data['card_number'])
        card = PaymentCard(
            user_id=data['user_id'],
            encrypted_card=encrypted,
            iv=iv,
            expiration_month=data['exp_month'],
            expiration_year=data['exp_year'],
            cardholder_name=data['cardholder_name']
        )
        db.session.add(card)
        db.session.commit()
        return jsonify({"message": "Card stored securely"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    cards = PaymentCard.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': c.id,
        'last4': decrypt_card(c.iv, c.encrypted_card)[-4:],
        'exp': f"{c.expiration_month}/{c.expiration_year}",
        'cardholder': c.cardholder_name
    } for c in cards])

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(ssl_context='adhoc')