from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from datetime import datetime

app = Flask(__name__)
# Use SQLite; tables will be created explicitly.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Generate an encryption key (in production, secure and manage your keys properly)
KEY = Fernet.generate_key()
fernet = Fernet(KEY)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Simulated logged-in user.
    encrypted_card_number = db.Column(db.String(512), nullable=False)
    name_on_card = db.Column(db.String(100))
    expiration_date = db.Column(db.String(10))
    billing_zip = db.Column(db.String(10))
    # Notice: CVV is intentionally not stored.

def validate_expiration_date(exp_date: str) -> bool:
    """
    Validate the expiration date.
    Accepts MM/YY or MM/YYYY formats.
    The card is considered valid through the end of the expiration month.
    """
    try:
        parts = exp_date.split('/')
        if len(parts) != 2:
            return False
        month_str, year_str = parts
        month = int(month_str)
        if month < 1 or month > 12:
            return False
        if len(year_str) == 2:
            # Convert to 4-digit year by assuming 2000-2099.
            year = 2000 + int(year_str)
        elif len(year_str) == 4:
            year = int(year_str)
        else:
            return False

        now = datetime.now()
        # The card is valid until the end of the expiration month.
        if now.year > year or (now.year == year and now.month > month):
            return False
        return True
    except Exception:
        return False

@app.route('/register_card', methods=['POST'])
def register_card():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input. JSON required.'}), 400

    # Verify all required input parameters are present.
    required_fields = ["card_number", "cvv", "expiration_date", "name_on_card", "billing_zip"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    # Extract fields from the input data.
    card_number = data["card_number"]
    cvv = data["cvv"]  # For demonstration only; do not store CVV in production!
    expiration_date = data["expiration_date"]
    name_on_card = data["name_on_card"]
    billing_zip = data["billing_zip"]

    # Validate the expiration date.
    if not validate_expiration_date(expiration_date):
        return jsonify({'error': 'Invalid expiration date. Format must be MM/YY or MM/YYYY and must not be expired.'}), 400

    # Encrypt the credit card number before storing it.
    encrypted_card_number = fernet.encrypt(card_number.encode()).decode()

    # In a real application, the logged-in user's ID should be determined from the session.
    user_id = 1

    new_card = PaymentCard(
        user_id=user_id,
        encrypted_card_number=encrypted_card_number,
        name_on_card=name_on_card,
        expiration_date=expiration_date,
        billing_zip=billing_zip
    )
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Card registered successfully', 'card_id': new_card.id}), 201

# For testing purposes only. Do not expose decrypted card numbers in production.
@app.route('/list_cards', methods=['GET'])
def list_cards():
    cards = PaymentCard.query.all()
    results = []
    for card in cards:
        try:
            decrypted_card_number = fernet.decrypt(card.encrypted_card_number.encode()).decode()
        except Exception:
            decrypted_card_number = "Decryption error"
        results.append({
            'card_id': card.id,
            'user_id': card.user_id,
            'card_number': decrypted_card_number,
            'name_on_card': card.name_on_card,
            'expiration_date': card.expiration_date,
            'billing_zip': card.billing_zip
        })
    return jsonify(results)

def run_tests():
    # Use Flask's test client to simulate requests.
    with app.test_client() as client:
        # Test registering a new card with a valid expiration date.
        payload = {
            "card_number": "4111111111111111",
            "cvv": "123",
            "expiration_date": "12/25",  # Format MM/YY
            "name_on_card": "John Doe",
            "billing_zip": "12345"
        }
        response = client.post('/register_card', json=payload)
        print("Response from /register_card (valid):", response.get_json())

        # Test with an expired date.
        payload["expiration_date"] = "01/20"  # Likely expired date.
        response = client.post('/register_card', json=payload)
        print("Response from /register_card (expired):", response.get_json())

        # Test listing all cards.
        response = client.get('/list_cards')
        print("Response from /list_cards:", response.get_json())

if __name__ == '__main__':
    # Create tables explicitly at startup.
    with app.app_context():
        db.drop_all()
        db.create_all()
    run_tests()
    # Uncomment the following line to run the Flask server.
    # app.run(debug=True)