# app.py (Backend)
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Generate key: Fernet.generate_key()
fernet = Fernet('your-encryption-key-here')  # Replace with your key

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # ... other user fields ...

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    encrypted_card_number = db.Column(db.BLOB, nullable=False)
    encrypted_expiry = db.Column(db.BLOB, nullable=False)
    encrypted_cvv = db.Column(db.BLOB, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('cards', lazy=True))

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        # In production, use proper authentication like Flask-Login
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        data = request.json
        # Basic validation
        if not all([data.get('card_number'), data.get('expiry'), data.get('cvv')]):
            return jsonify({'error': 'Missing fields'}), 400

        # Encrypt sensitive data
        try:
            encrypted_number = fernet.encrypt(data['card_number'].encode())
            encrypted_expiry = fernet.encrypt(data['expiry'].encode())
            encrypted_cvv = fernet.encrypt(data['cvv'].encode())
        except Exception as e:
            return jsonify({'error': 'Encryption failed'}), 500

        # Save to database
        new_card = PaymentCard(
            user_id=session['user_id'],
            encrypted_card_number=encrypted_number,
            encrypted_expiry=encrypted_expiry,
            encrypted_cvv=encrypted_cvv
        )
        db.session.add(new_card)
        db.session.commit()

        return jsonify({'message': 'Card added successfully'}), 201

    return render_template('add_card.html')

# Test route - remove in production
@app.route('/test_login/<username>')
def test_login(username):
    user = User.query.filter_by(username=username).first()
    if user:
        session['user_id'] = user.id
        return f'Logged in as {username}'
    return 'User not found'

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)