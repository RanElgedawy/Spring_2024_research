# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, validators
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(19), nullable=False)
    expiration_month = db.Column(db.Integer, nullable=False)
    expiration_year = db.Column(db.Integer, nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Form Class
class AddCardForm(FlaskForm):
    card_number = StringField('Card Number', [
        validators.Length(min=13, max=19, message='Invalid card number length'),
        validators.Regexp(r'^\d+$', message='Card number must contain only numbers')
    ])
    expiration_month = SelectField('Expiration Month', 
        choices=[(str(i), f'{i:02d}') for i in range(1,13)],
        validators=[validators.InputRequired()]
    )
    expiration_year = SelectField('Expiration Year', 
        choices=[(str(i), str(i)) for i in range(datetime.datetime.now().year, datetime.datetime.now().year+11)],
        validators=[validators.InputRequired()]
    )
    cvv = StringField('CVV', [
        validators.Length(min=3, max=4, message='CVV must be 3 or 4 digits'),
        validators.Regexp(r'^\d+$', message='CVV must contain only numbers')
    ])

# Routes
@app.route('/login-mock')  # Mock login for testing
def login_mock():
    session['user_id'] = 1  # Simulate logged in user
    return redirect(url_for('add_card'))

@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('login_mock'))
    
    form = AddCardForm()
    if form.validate_on_submit():
        card = PaymentCard(
            user_id=session['user_id'],
            card_number=form.card_number.data,
            expiration_month=int(form.expiration_month.data),
            expiration_year=int(form.expiration_year.data),
            cvv=form.cvv.data
        )
        db.session.add(card)
        db.session.commit()
        return 'Card added successfully! <a href="/add-card">Add another</a>'
    
    return render_template('add_card.html', form=form)

# Test Route (Remove in production)
@app.route('/cards')
def list_cards():
    cards = PaymentCard.query.all()
    return render_template('cards.html', cards=cards)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)