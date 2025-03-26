from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Add more user-related fields as needed

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)  # Format: MM/YY
    cvv = db.Column(db.String(3), nullable=False)
    name_on_card = db.Column(db.String(100), nullable=False)
    billing_zip_code = db.Column(db.String(10), nullable=False)
    # Add more card-related fields as needed

@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.json
    user_id = data.get('user_id')
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')
    name_on_card = data.get('name_on_card')
    billing_zip_code = data.get('billing_zip_code')

    # Validate input
    if not all([user_id, card_number, expiry_date, cvv, name_on_card, billing_zip_code]):
        return jsonify({'message': 'Missing required fields'}), 400

    # Validate expiration date format and future date
    try:
        expiry_date = datetime.strptime(expiry_date, '%m/%y')
        if expiry_date < datetime.now():
            raise ValueError
    except ValueError:
        return jsonify({'message': 'Invalid expiration date or expired'}), 400

    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Add the card
    new_card = PaymentCard(user_id=user_id, card_number=card_number, expiry_date=expiry_date.strftime('%m/%y'), 
                           cvv=cvv, name_on_card=name_on_card, billing_zip_code=billing_zip_code)
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Card added successfully'}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Check if sample user already exists
        sample_user = User.query.filter_by(email='sample@example.com').first()
        if not sample_user:
            # Insert sample user data
            sample_user = User(username='sample_user', email='sample@example.com')
            db.session.add(sample_user)
            db.session.commit()

            # Insert sample payment card data
            sample_card = PaymentCard(user_id=sample_user.id, card_number='1234567890123456',
                                      expiry_date='12/25', cvv='123', name_on_card='John Doe', billing_zip_code='12345')
            db.session.add(sample_card)
            db.session.commit()

    app.run(debug=True)