from flask import Flask, request, jsonify, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from datetime import datetime
import warnings

# Suppress SQLAlchemy warning about track modifications
warnings.filterwarnings("ignore", category=DeprecationWarning)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-sessions'  # In production, use proper secret management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Generate encryption key (In production, use proper key management!)
# Never commit actual encryption keys to version control!
FERNET_KEY = Fernet.generate_key()
cipher_suite = Fernet(FERNET_KEY)

db = SQLAlchemy(app)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number_encrypted = db.Column(db.LargeBinary, nullable=False)
    expiration_month = db.Column(db.String(2), nullable=False)
    expiration_year = db.Column(db.String(4), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def decrypt_card_number(self):
        return cipher_suite.decrypt(self.card_number_encrypted).decode()

# Create database tables
with app.app_context():
    db.create_all()

# Mock authentication - assumes user is already logged in
@app.route('/mock_login/<int:user_id>')
def mock_login(user_id):
    session['user_id'] = user_id
    return f"Mock logged in as user {user_id}"

@app.route('/add_card', methods=['POST'])
def add_payment_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    required_fields = ['card_number', 'exp_month', 'exp_year', 'cardholder_name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Encrypt sensitive data
        encrypted_card = cipher_suite.encrypt(data['card_number'].encode())
        
        new_card = PaymentCard(
            user_id=session['user_id'],
            card_number_encrypted=encrypted_card,
            expiration_month=data['exp_month'],
            expiration_year=data['exp_year'],
            cardholder_name=data['cardholder_name']
        )
        
        db.session.add(new_card)
        db.session.commit()
        return jsonify({'message': 'Card added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/cards')
def get_cards():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    cards = PaymentCard.query.filter_by(user_id=session['user_id']).all()
    return jsonify([
        {
            'id': card.id,
            'card_number': card.decrypt_card_number(),
            'expiration': f"{card.expiration_month}/{card.expiration_year}",
            'cardholder_name': card.cardholder_name
        } for card in cards
    ])

# Test HTML form
TEST_FORM = """
<!DOCTYPE html>
<html>
<body>
    <h2>Add Payment Card (Test)</h2>
    <form onsubmit="event.preventDefault(); submitForm();">
        Card Number: <input type="text" id="card_number" required><br>
        Exp Month (MM): <input type="text" id="exp_month" required><br>
        Exp Year (YYYY): <input type="text" id="exp_year" required><br>
        Cardholder Name: <input type="text" id="cardholder_name" required><br>
        CVV: <input type="text" id="cvv" required><br>
        <button type="submit">Submit</button>
    </form>
    <div id="result"></div>
    <script>
        async function submitForm() {
            const data = {
                card_number: document.getElementById('card_number').value,
                exp_month: document.getElementById('exp_month').value,
                exp_year: document.getElementById('exp_year').value,
                cardholder_name: document.getElementById('cardholder_name').value
            };
            
            const response = await fetch('/add_card', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            document.getElementById('result').innerHTML = 
                `Status: ${response.status} - ${JSON.stringify(result)}`;
        }
    </script>
</body>
</html>
"""

@app.route('/test_form')
def test_form():
    return render_template_string(TEST_FORM)

if __name__ == '__main__':
    app.run(debug=True)