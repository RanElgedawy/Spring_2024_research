from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
db = SQLAlchemy(app)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(128), unique=True, nullable=False)
    last_four = db.Column(db.String(4), nullable=False)
    expiry_month = db.Column(db.Integer, nullable=False)
    expiry_year = db.Column(db.Integer, nullable=False)

# Assuming a User model exists
class User(db.Model):
    # ... your User model fields

@app.route('/register_card', methods=['POST'])
def register_card():
    user_id = request.json.get('user_id')
    card_number = request.json.get('card_number')
    # ... other card details

    # Generate a random token
    token = secrets.token_urlsafe(64)

    # Store the token and last four digits
    card = Card(user_id=user_id, token=token, last_four=card_number[-4:])
    # ... store other card details

    db.session.add(card)
    db.session.commit()

    return jsonify({'message': 'Card registered successfully', 'token': token})

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)