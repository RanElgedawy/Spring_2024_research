from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'
db = SQLAlchemy(app)

# Generate a secure encryption key
key = Fernet.generate_key()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    card_number = db.Column(db.String(16))
    cardholder_name = db.Column(db.String(100))
    expiration_date = db.Column(db.String(7))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"<PaymentCard {self.id}>"

def validate_expiration_date(expiration_date):
    try:
        month, year = expiration_date.split('/')
        month = int(month)
        year = int(year)

        # Pad the year with leading zeros if necessary
        year_str = str(year).zfill(4)

        # Get the current year
        current_year = datetime.datetime.now().year

        # Check month and year
        if not (1 <= month <= 12) or year_str < str(current_year):
            return False

        return True
    except ValueError:
        # Handle invalid format
        return False
    
@app.route('/payment-cards', methods=['POST'])
def add_payment_card():
    data = request.get_json()

    # Verify required input parameters
    required_fields = ['card_number', 'cardholder_name', 'expiration_date', 'cvv', 'billing_zip_code']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
        # Validate expiration date
    if not validate_expiration_date(data['expiration_date']):
        return jsonify({'error': 'Invalid expiration date'}), 400
    
    card_number = data['card_number']
    # Encrypt the card number
    encrypted_card_number = Fernet(key).encrypt(card_number.encode())

    payment_card = PaymentCard(
        user_id=data['user_id'],
        card_number=encrypted_card_number,
        cardholder_name=data['cardholder_name'],
        expiration_date=data['expiration_date']
    )
    db.session.add(payment_card)
    db.session.commit()

    return jsonify({'message': 'Payment card added successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)