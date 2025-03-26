from flask import Flask, render_template, request, redirect, url_for
from flask_login import UserMixin, LoginManager
import stripe
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField
from decimal import Decimal
from flask_wtf import FlaskForm
import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # ... (other user attributes)
    card_details = db.Column(db.String)  # Store encrypted card details
    address = db.relationship('Address', backref='user', uselist=False)


    def get_id(self):
        return self.id

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # ... (other cart attributes)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    product_price = db.Column(db.Float)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)  # Use Float instead of Decimal
    created_at = db.Column(db.DateTime)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    total_amount = db.Column(db.Float)  # Use Float instead of Decimal
    status = db.Column(db.String, default='pending')  # Initial status
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class CheckoutForm(FlaskForm):
    shipping_address = StringField('Shipping Address')
    city = StringField('City')
    state = StringField('State/Province')
    zip_code = StringField('ZIP/Postal Code')
    country = StringField('Country')
    submit = SubmitField('Checkout')

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shipping_address = db.Column(db.String)
    city = db.Column(db.String)
    state = db.Column(db.String)
    zip_code = db.Column(db.String)
    country = db.Column(db.String)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# Configure Stripe
stripe.api_key = 'your_stripe_secret_key'

def calculate_total(cart):
    total = 0
    for item in cart.items:
        total += item.product.price * item.quantity
    total += 20  # Add shipping fee
    return total

def process_payment(card_details, total):
    try:
        # Replace with actual Stripe payment processing logic
        charge = stripe.Charge.create(
            amount=total * 100,  # Convert to cents
            currency='usd',
            source=card_details,
            description='E-commerce Purchase'
        )
        return {'success': True, 'charge_id': charge.id}
    except stripe.error.CardError as e:
        return {'success': False, 'error': e.message}

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    form = CheckoutForm()
    if form.validate_on_submit():
        # Check if user is logged in using Flask-Login
        if login_manager.user:
            user = login_manager.user
            total = calculate_total(user.cart)
            payment_result = process_payment(user.card_details, total)

            if payment_result.success:
                # Store address information
                user.address = Address(
                    shipping_address=form.shipping_address.data,
                    city=form.city.data,
                    state=form.state.data,
                    zip_code=form.zip_code.data,
                    country=form.country.data
                )

                # Create and update order
                transaction = Transaction(user_id=user.id, amount=total)
                order = Order(user_id=user.id, total_amount=total)
                order.status = 'processing'  # Update status here

                db.session.add(transaction)
                db.session.add(order)
                db.session.add(user.address)  # Add address to session
                db.session.commit()

                return redirect(url_for('checkout_success'))
            else:
                return render_template('checkout_failed.html', error=payment_result.error)
        else:
            # Redirect to login page or display message
            return redirect(url_for('login'))

    return render_template('checkout.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)