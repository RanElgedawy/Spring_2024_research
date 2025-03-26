from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # for session handling

db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # other user fields such as hashed_password, etc.

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), nullable=False)
    expiry = db.Column(db.String(7), nullable=False)  # e.g. "MM/YYYY"
    cvv = db.Column(db.String(4), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('payment_cards', lazy=True))

# --- Helper: Initialize Database and Create a Dummy User ---
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()
    # Create a dummy user if not exists
    if not User.query.filter_by(username="demo_user").first():
        demo_user = User(username="demo_user")
        db.session.add(demo_user)
        db.session.commit()

# --- Endpoints ---

# Dummy login endpoint for testing.
# In a real app, you would have proper authentication.
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if user:
        session['user_id'] = user.id
        return jsonify({"message": f"Logged in as {username}", "user_id": user.id})
    else:
        return jsonify({"message": "User not found"}), 404

# Endpoint to add a new payment card for the logged in user.
@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({"message": "User not logged in"}), 401

    data = request.get_json()
    card_number = data.get('card_number')
    expiry = data.get('expiry')
    cvv = data.get('cvv')
    cardholder_name = data.get('cardholder_name')

    if not all([card_number, expiry, cvv, cardholder_name]):
        return jsonify({"message": "Missing card information"}), 400

    new_card = PaymentCard(
        card_number=card_number,
        expiry=expiry,
        cvv=cvv,
        cardholder_name=cardholder_name,
        user_id=session['user_id']
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({"message": "Payment card added successfully", "card_id": new_card.id}), 201

# --- Testing Code ---
# This test function uses the Flask test client to simulate login and add a card.
def run_tests():
    with app.test_client() as client:
        # Login with our dummy user
        login_response = client.post('/login', json={"username": "demo_user"})
        print("Login Response:", login_response.get_json())

        # Add a card
        card_data = {
            "card_number": "4111111111111111",
            "expiry": "12/2026",
            "cvv": "123",
            "cardholder_name": "John Doe"
        }
        add_card_response = client.post('/add_card', json=card_data)
        print("Add Card Response:", add_card_response.get_json())

        # Retrieve card details from DB to verify (for testing)
        from pprint import pprint
        user_id = login_response.get_json()['user_id']
        cards = PaymentCard.query.filter_by(user_id=user_id).all()
        print("Stored Cards for user_id", user_id)
        for card in cards:
            pprint({
                "id": card.id,
                "card_number": card.card_number,
                "expiry": card.expiry,
                "cvv": card.cvv,
                "cardholder_name": card.cardholder_name
            })

if __name__ == '__main__':
    # Uncomment the following line to run tests automatically:
    # run_tests()
    
    # Otherwise, run the Flask app:
    app.run(debug=True)
