from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_required
from cryptography.fernet import Fernet
import os
import datetime

# Initialize app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@localhost/payment_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Generate encryption key once (store securely in production!)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add other user fields as needed

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    encrypted_card_number = db.Column(db.LargeBinary, nullable=False)
    expiration_month = db.Column(db.String(2), nullable=False)
    expiration_year = db.Column(db.String(4), nullable=False)
    last_four = db.Column(db.String(4), nullable=False)  # For display purposes
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def decrypt_card_number(self):
        return cipher_suite.decrypt(self.encrypted_card_number).decode()

# Create tables
with app.app_context():
    db.create_all()

# Helper functions
def encrypt_card_data(card_number):
    return cipher_suite.encrypt(card_number.encode())

def validate_card_data(data):
    # Add more validation as needed
    if not all(k in data for k in ('card_number', 'exp_month', 'exp_year')):
        return False
    if len(data['card_number']) < 13 or len(data['card_number']) > 19:
        return False
    return True

# API Endpoints
@app.route('/api/payment-methods', methods=['POST'])
@login_required
def add_payment_method():
    data = request.get_json()
    
    if not validate_card_data(data):
        return jsonify({'error': 'Invalid card data'}), 400
    
    try:
        # Never store CVV!
        encrypted_card = encrypt_card_data(data['card_number'])
        last_four = data['card_number'][-4:]

        new_card = PaymentCard(
            user_id=current_user.id,
            encrypted_card_number=encrypted_card,
            expiration_month=data['exp_month'],
            expiration_year=data['exp_year'],
            last_four=last_four
        )

        db.session.add(new_card)
        db.session.commit()
        return jsonify({'message': 'Card added successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Test Endpoints
@app.route('/test/login', methods=['POST'])
def test_login():
    # For testing purposes only - implement proper auth in production
    user = User.query.first()
    return jsonify({'user_id': user.id})

if __name__ == '__main__':
    app.run(debug=True)