from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    cards = db.relationship('Card', backref='user')

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Other card details (e.g., cardholder name, expiration date)

@app.route('/register-card', methods=['GET', 'POST'])
def register_card():
    if request.method == 'POST':
        # Get card details from the form
        card_number = request.form['card_number']
        # ... other card details

        # Generate a random token
        token = secrets.token_hex(16)

        # Create a new card record with the token
        card = Card(token=token, user_id=current_user.id)
        db.session.add(card)
        db.session.commit()

        # Store the actual card details securely (e.g., using a payment gateway)

        return redirect(url_for('success'))  # Redirect to a success page
    else:
        return render_template('register_card.html')

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)