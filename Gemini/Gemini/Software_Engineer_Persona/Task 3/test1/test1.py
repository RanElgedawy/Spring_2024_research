from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    cards = db.relationship('Card', backref='user')

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)
    expiration_date = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Assuming you have a login system in place
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        card_number = request.form['card_number']
        expiration_date = request.form['expiration_date']
        cvv = request.form['cvv']
        name_on_card = request.form['name_on_card']
        billing_zip = request.form['billing_zip']

        # Input validation
        if not all([card_number, expiration_date, cvv, name_on_card, billing_zip]):
            return render_template('add_card.html', error="Please fill in all required fields.")
        
        try:
            expiration_date = datetime.datetime.strptime(request.form['expiration_date'], '%m/%y')
        except ValueError:
            return render_template('add_card.html', error="Invalid expiration date format.")

        if expiration_date < datetime.datetime.now():
            return render_template('add_card.html', error="Expiration date cannot be in the past.")
    
        
        # Tokenize or encrypt card details for security
        tokenized_card = f"token_{card_number}"

        existing_card = Card.query.filter_by(card_number=tokenized_card).first()
        if existing_card:
            return render_template('add_card.html', error="Card number already exists.")
        
        new_card = Card(card_number=tokenized_card, expiration_date=expiration_date, cvv=cvv, user_id=1)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('success'))

    return render_template('add_card.html')

@app.route('/success')
def success():
    return "Card added successfully!"

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)