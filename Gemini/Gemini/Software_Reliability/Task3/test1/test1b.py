from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()

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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
db.init_app(app)

@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        card_number = request.form['card_number']
        expiration_date = request.form['expiration_date']
        cvv = request.form['cvv']

        # Assuming user is logged in and user_id is available
        user = User.query.get(user_id)

        new_card = Card(card_number=card_number, expiration_date=expiration_date, cvv=cvv, user=user)
        db.session.add(new_card)
        db.session.commit()

        return redirect(url_for('success'))

    return render_template('add_card.html')

@app.route('/success')
def success():
    return 'Card added successfully!'

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)