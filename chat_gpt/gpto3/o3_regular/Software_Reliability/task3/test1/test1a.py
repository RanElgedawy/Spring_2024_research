from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
# Set a secret key for session management
app.config['SECRET_KEY'] = 'your-secret-key'
# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the User model (assuming users are already registered)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    # Relationship to payment cards
    payment_cards = db.relationship('PaymentCard', backref='user', lazy=True)

# Define the PaymentCard model
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), nullable=False)
    expiry_date = db.Column(db.String(7), nullable=False)  # Format "MM/YYYY"
    cvv = db.Column(db.String(4), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Automatically create tables before the first request
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()
    # For testing, create a dummy user if not already present.
    if not User.query.filter_by(username='testuser').first():
        test_user = User(username='testuser')
        db.session.add(test_user)
        db.session.commit()

# Dummy login route for testing (assumes the user "testuser" exists)
@app.route('/login', methods=['GET'])
def login():
    username = request.args.get('username', 'testuser')
    user = User.query.filter_by(username=username).first()
    if user:
        session['user_id'] = user.id
        return jsonify({"message": f"Logged in as {username}", "user_id": user.id})
    return jsonify({"error": "User not found"}), 404

# Route to add a new payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    # Retrieve payment card data from JSON body (or form data)
    data = request.get_json() or request.form
    card_number = data.get('card_number')
    expiry_date = data.get('expiry_date')
    cvv = data.get('cvv')
    cardholder_name = data.get('cardholder_name')

    # Validate required fields
    if not all([card_number, expiry_date, cvv, cardholder_name]):
        return jsonify({"error": "Missing payment card information"}), 400

    # Create a new PaymentCard entry associated with the logged-in user
    new_card = PaymentCard(
        card_number=card_number,
        expiry_date=expiry_date,
        cvv=cvv,
        cardholder_name=cardholder_name,
        user_id=session['user_id']
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({"message": "Payment card added successfully", "card_id": new_card.id})

# Route to list all payment cards for the logged-in user (for testing)
@app.route('/cards', methods=['GET'])
def get_cards():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    user_id = session['user_id']
    cards = PaymentCard.query.filter_by(user_id=user_id).all()
    cards_data = [{
        "id": card.id,
        "card_number": card.card_number,
        "expiry_date": card.expiry_date,
        "cvv": card.cvv,
        "cardholder_name": card.cardholder_name,
        "created_at": card.created_at.isoformat()
    } for card in cards]
    return jsonify(cards_data)

# Run the app
if __name__ == '__main__':
    # For testing purposes, run the server in debug mode
    app.run(debug=True)
