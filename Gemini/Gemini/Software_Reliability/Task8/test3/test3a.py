from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import stripe  # Assuming Stripe for payment processing

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# Model definitions (corresponding to the database schema)
class User(db.Model):
    # ...

class Product(db.Model):
    # ...

class CartItem(db.Model):
    # ...

class Order(db.Model):
    # ...

class Transaction(db.Model):
    # ...

# ... (other model definitions)

@app.route('/checkout', methods=['POST'])
def checkout():
    user_id = request.form['user_id']
    user = User.query.get(user_id)
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    total_price = 20  # Shipping fee
    for item in cart_items:
        total_price += item.quantity * item.product.price

    # Simulate payment processing with Stripe (replace with actual integration)
    stripe.api_key = 'YOUR_STRIPE_SECRET_KEY'
    charge = stripe.Charge.create(
        amount=int(total_price * 100),
        currency='usd',
        source=request.form['stripeToken']
    )

    if charge['status'] == 'succeeded':
        order = Order(user_id=user_id, total_price=total_price)
        db.session.add(order)
        db.session.commit()

        transaction = Transaction(order_id=order.id, payment_method='Stripe', amount=total_price)
        db.session.add(transaction)
        db.session.commit()

        # Clear the user's cart
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        return render_template('checkout_success.html')
    else:
        return render_template('checkout_failure.html')

if __name__ == '__main__':
    app.run(debug=True)