from flask_sqlalchemy import SQLAlchemy
import stripe

stripe.api_key = 'your_stripe_secret_key'

db = SQLAlchemy()

class User(db.Model):
    # ... (define your User model)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total = db.Column(db.Float)
    # ... (add other fields as needed)

with app.app_context():
    db.drop_all()
    db.create_all()

def create_checkout_session(items, user_email):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {'price': item['price'], 'quantity': item['quantity']} for item in items
        ],
        mode='payment',
        success_url='https://your-website.com/success',
        cancel_url='https://your-website.com/cancel',
        customer_email=user_email
    )
    return session.id