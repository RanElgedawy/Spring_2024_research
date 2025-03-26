from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'
db = SQLAlchemy(app)

# Create a model for storing tokenized card information
class TokenizedCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(128), unique=True, nullable=False)
    encrypted_card_data = db.Column(db.String(1024), nullable=False)

# Generate a random token
def generate_token():
    return secrets.token_urlsafe(16)

# Encrypt card data
def encrypt_card_data(card_data, encryption_key):
    cipher = Fernet(encryption_key)
    encrypted_data = cipher.encrypt(card_data.encode())
    return encrypted_data.decode()

# Decrypt card data (for testing or authorized operations)
def decrypt_card_data(encrypted_data, encryption_key):
    cipher = Fernet(encryption_key)
    decrypted_data = cipher.decrypt(encrypted_data.encode())
    return decrypted_data.decode()

# Endpoint to register a new card
@app.route('/register_card', methods=['POST'])
def register_card():
    card_data = request.json
    token = generate_token()
    encrypted_card_data = encrypt_card_data(card_data, encryption_key)

    new_card = TokenizedCard(token=token, encrypted_card_data=encrypted_card_data)
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Card registered successfully', 'token': token})

# Testing
if __name__ == '__main__':
    # Generate a strong encryption key
    encryption_key = Fernet.generate_key()

    # Create database tables
    with app.app_context():
        db.drop_all()
        db.create_all()

    app.run(debug=True)