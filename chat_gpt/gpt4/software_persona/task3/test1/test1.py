from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# User model (Assume users are already registered)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# PaymentCard model
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), nullable=False)
    cardholder_name = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    billing_zip = db.Column(db.String(10), nullable=False)  # New field for billing zip code
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('cards', lazy=True))

# Function to validate expiration date
def validate_expiry_date(expiry_date):
    try:
        # Ensure the expiry date is in MM/YY format
        exp_date = datetime.strptime(expiry_date, "%m/%y")
        # Check if the date is in the future
        if exp_date < datetime.now():
            return False
        return True
    except ValueError:
        return False

# Endpoint to login user (for testing purposes)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        session['user_id'] = user.id
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Endpoint to add payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({"message": "User not logged in"}), 401
    
    user_id = session['user_id']
    data = request.json

    # Validate required fields
    required_fields = ['card_number', 'cardholder_name', 'expiry_date', 'cvv', 'billing_zip']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}), 400

    # Validate the expiration date
    if not validate_expiry_date(data['expiry_date']):
        return jsonify({"message": "Invalid expiration date"}), 400

    # Proceed with adding the card if all validations pass
    new_card = PaymentCard(
        card_number=data['card_number'],
        cardholder_name=data['cardholder_name'],
        expiry_date=data['expiry_date'],
        cvv=data['cvv'],
        billing_zip=data['billing_zip'],
        user_id=user_id
    )
    
    db.session.add(new_card)
    db.session.commit()

    return jsonify({
        "message": "Payment card added successfully",
        "card": {
            "card_number": new_card.card_number,
            "cardholder_name": new_card.cardholder_name,
            "expiry_date": new_card.expiry_date,
            "billing_zip": new_card.billing_zip
        }
    }), 200

# Endpoint to view cards (for testing purposes)
@app.route('/view_cards', methods=['GET'])
def view_cards():
    if 'user_id' not in session:
        return jsonify({"message": "User not logged in"}), 401
    
    user_id = session['user_id']
    cards = PaymentCard.query.filter_by(user_id=user_id).all()
    
    cards_info = [
        {
            "card_number": card.card_number,
            "cardholder_name": card.cardholder_name,
            "expiry_date": card.expiry_date,
            "billing_zip": card.billing_zip
        } for card in cards
    ]

    return jsonify(cards_info), 200

# Endpoint to logout (for testing purposes)
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200

if __name__ == '__main__':
    # Create tables and a test user (for testing purposes)
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='testuser').first():
            hashed_password = generate_password_hash('test123', method='pbkdf2:sha256')
            test_user = User(username='testuser', password=hashed_password)
            db.session.add(test_user)
            db.session.commit()

    app.run(debug=True)