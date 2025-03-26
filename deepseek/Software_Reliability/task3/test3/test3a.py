from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Change for production
db = SQLAlchemy(app)

# Payment Card Model
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)  # MM/YY
    cvv = db.Column(db.String(3), nullable=False)
    cardholder_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'card_number': f'**** **** **** {self.card_number[-4:]}',
            'expiry_date': self.expiry_date,
            'cardholder_name': self.cardholder_name
        }

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Validation helpers
def validate_card_data(data):
    if not re.match(r'^\d{16}$', data['card_number']):
        return False
    if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', data['expiry_date']):
        return False
    if not re.match(r'^\d{3}$', data['cvv']):
        return False
    return True

@app.route('/add-card', methods=['POST'])
def add_card():
    # In production: Check user authentication here
    data = request.get_json()
    
    if not validate_card_data(data):
        return jsonify({'error': 'Invalid card data'}), 400
        
    try:
        card = PaymentCard(
            user_id=1,  # Replace with actual user ID from session
            card_number=data['card_number'],
            expiry_date=data['expiry_date'],
            cvv=data['cvv'],
            cardholder_name=data['cardholder_name']
        )
        db.session.add(card)
        db.session.commit()
        return jsonify(card.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/card-form')
def card_form():
    return render_template('card_form.html')

if __name__ == '__main__':
    app.run(debug=True)