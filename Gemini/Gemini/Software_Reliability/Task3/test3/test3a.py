from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/ecommerce'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    cards = db.relationship('Card', backref='user')

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    card_number = db.Column(db.String(16), nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    cvv = db.Column(db.String(3), nullable=False)

# Create database tables if they don't exist
with app.app_context():
    db.drop_all()
    db.create_all()

# Route to handle card addition
@app.route('/add-card', methods=['POST'])
def add_card():
    data = request.get_json()
    card_number = data.get('card_number')
    expiration_date = data.get('expiration_date')
    cvv = data.get('cvv')

    # Validate card details
    if not card_number or not expiration_date or not cvv:
        return jsonify({'error': 'Invalid card details'}), 400

    # Check if user is logged in
    # ... (implement authentication logic)

    # Create a new card object
    new_card = Card(card_number=card_number, expiration_date=expiration_date, cvv=cvv)
    db.session.add(new_card)
    db.session.commit()

    return jsonify({'message': 'Card added successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)