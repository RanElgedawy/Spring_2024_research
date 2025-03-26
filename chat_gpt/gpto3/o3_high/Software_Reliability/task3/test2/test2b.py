from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import sys

app = Flask(__name__)
# Configure the SQLite database and secret key for sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# Define a PaymentCard model to store card details
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(20), nullable=False)  # In practice, do not store raw card numbers.
    expiration_date = db.Column(db.String(7), nullable=False)  # Format: MM/YYYY
    cvv = db.Column(db.String(4), nullable=False)
    card_holder_name = db.Column(db.String(100), nullable=False)

# Dummy login route to simulate a logged-in user.
@app.route('/login', methods=['POST'])
def login():
    # For testing, we expect a JSON body with "user_id"
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    session['user_id'] = user_id
    return jsonify({"message": "Logged in", "user_id": user_id}), 200

# Route to add a new payment card for a logged-in user.
@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    # Extract card details from the request
    card_number = data.get('card_number')
    expiration_date = data.get('expiration_date')
    cvv = data.get('cvv')
    card_holder_name = data.get('card_holder_name')

    # Basic validation to ensure all fields are provided
    if not all([card_number, expiration_date, cvv, card_holder_name]):
        return jsonify({"error": "Missing card information"}), 400

    # Create and save the new card record
    new_card = PaymentCard(
        user_id=session['user_id'],
        card_number=card_number,
        expiration_date=expiration_date,
        cvv=cvv,
        card_holder_name=card_holder_name
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({"message": "Card added successfully", "card_id": new_card.id}), 200

# A simple test function to check if adding a card works.
def run_tests():
    with app.test_client() as client:
        # First, simulate logging in
        login_response = client.post('/login', json={"user_id": 1})
        print("Login Response:", login_response.json)

        # Now, add a card for the logged-in user
        add_card_response = client.post('/add_card', json={
            "card_number": "4111111111111111",
            "expiration_date": "12/2024",
            "cvv": "123",
            "card_holder_name": "John Doe"
        })
        print("Add Card Response:", add_card_response.json)

if __name__ == '__main__':
    # Create database tables if they do not exist
    db.drop_all()
    db.create_all()

    # If run with the "test" argument, execute the test routine
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        # Otherwise, start the Flask development server
        app.run(debug=True)
