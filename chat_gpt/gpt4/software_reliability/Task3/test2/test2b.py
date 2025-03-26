from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the User model (assuming users are already registered)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)

# Define the PaymentCard model
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    card_holder_name = db.Column(db.String(50), nullable=False)
    expiration_date = db.Column(db.String(5), nullable=False)  # Format: MM/YY
    cvv = db.Column(db.String(3), nullable=False)

    user = db.relationship('User', backref='payment_cards')

# Create the database tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Route to add a new payment card
@app.route('/add_card', methods=['POST'])
def add_card():
    data = request.json
    user_id = data.get('user_id')
    card_number = data.get('card_number')
    card_holder_name = data.get('card_holder_name')
    expiration_date = data.get('expiration_date')
    cvv = data.get('cvv')

    # Validate input data
    if not all([user_id, card_number, card_holder_name, expiration_date, cvv]):
        return jsonify({"error": "All fields are required"}), 400

    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Save the payment card
    new_card = PaymentCard(
        user_id=user_id,
        card_number=card_number,
        card_holder_name=card_holder_name,
        expiration_date=expiration_date,
        cvv=cvv
    )

    try:
        db.session.add(new_card)
        db.session.commit()
        return jsonify({"message": "Payment card added successfully"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to add payment card"}), 500

# Route to get all payment cards (for testing purposes)
@app.route('/get_cards', methods=['GET'])
def get_cards():
    cards = PaymentCard.query.all()
    return jsonify([
        {
            "id": card.id,
            "user_id": card.user_id,
            "card_number": card.card_number,
            "card_holder_name": card.card_holder_name,
            "expiration_date": card.expiration_date
        } for card in cards
    ]), 200

# Add a route to create a sample user (for testing purposes)
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = User(username=username)

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User created successfully", "user_id": user.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User already exists"}), 400

if __name__ == '__main__':
    app.run(debug=True)