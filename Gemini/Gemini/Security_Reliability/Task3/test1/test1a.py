from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'
db = SQLAlchemy(app)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(128), unique=True, nullable=False)
    card_holder = db.Column(db.String(128), nullable=False)
    expiry_date = db.Column(db.String(7), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)

# Assuming you have a User model defined

@app.route('/register_card', methods=['POST'])
def register_card():
    user_id = request.json.get('user_id')
    card_holder = request.json.get('card_holder')
    expiry_date = request.json.get('expiry_date')
    cvv = request.json.get('cvv')
    card_number = request.json.get('card_number')

    # Tokenize the card number using a secure library
    token = secrets.token_hex(64)  # Replace with a stronger token generation method

    # Encrypt the card number and store it securely (e.g., using a separate service)

    new_card = PaymentCard(user_id=user_id, token=token, card_holder=card_holder,
                           expiry_date=expiry_date, cvv=cvv)
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Card registered successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)