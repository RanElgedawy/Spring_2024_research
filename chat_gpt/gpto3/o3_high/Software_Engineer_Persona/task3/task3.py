from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Configure the SQLite database.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the PaymentCard model with all required fields.
class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    card_holder = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(7), nullable=False)  # Expected format: MM/YYYY
    cvv = db.Column(db.String(4), nullable=False)
    billing_zip = db.Column(db.String(10), nullable=False)

# Dummy function to simulate a logged-in user.
def get_current_user_id():
    return 1  # Replace with your authentication mechanism as needed.

# Validate the expiration date.
def validate_expiration_date(exp_date_str):
    """
    Validates that the expiration date is in MM/YYYY format and is not expired.
    """
    try:
        # Split and convert the input.
        month, year = map(int, exp_date_str.split('/'))
        if month < 1 or month > 12:
            return False

        now = datetime.now()
        # Check if the year is in the future or, if it's this year, that the month is not past.
        if year < now.year:
            return False
        if year == now.year and month < now.month:
            return False
        return True
    except ValueError:
        return False

# Route to add a new payment card.
@app.route('/add-card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        user_id = get_current_user_id()
        card_number = request.form.get('card_number')
        card_holder = request.form.get('card_holder')
        expiration_date = request.form.get('expiration_date')
        cvv = request.form.get('cvv')
        billing_zip = request.form.get('billing_zip')

        # Verify that all expected parameters are provided.
        if not all([card_number, card_holder, expiration_date, cvv, billing_zip]):
            return "Missing one or more required fields.", 400

        # Validate the expiration date.
        if not validate_expiration_date(expiration_date):
            return ("Invalid expiration date. Please ensure it is in the format MM/YYYY "
                    "and that the card has not expired."), 400

        # Create a new PaymentCard instance.
        new_card = PaymentCard(
            user_id=user_id,
            card_number=card_number,
            card_holder=card_holder,
            expiration_date=expiration_date,
            cvv=cvv,
            billing_zip=billing_zip
        )
        db.session.add(new_card)
        db.session.commit()

        return redirect(url_for('list_cards'))

    # GET: Render a simple HTML form to add the card.
    form_html = '''
    <h2>Add a Payment Card</h2>
    <form method="POST">
        <label>Card Number:</label><br>
        <input type="text" name="card_number" maxlength="16" required><br><br>
        <label>Name on Card:</label><br>
        <input type="text" name="card_holder" required><br><br>
        <label>Expiration Date (MM/YYYY):</label><br>
        <input type="text" name="expiration_date" pattern="(0[1-9]|1[0-2])\/\d{4}" placeholder="MM/YYYY" required><br><br>
        <label>CVV:</label><br>
        <input type="text" name="cvv" maxlength="4" required><br><br>
        <label>Billing Zip Code:</label><br>
        <input type="text" name="billing_zip" maxlength="10" required><br><br>
        <input type="submit" value="Add Card">
    </form>
    '''
    return render_template_string(form_html)

# Route to list all payment cards for the current user.
@app.route('/cards')
def list_cards():
    user_id = get_current_user_id()
    cards = PaymentCard.query.filter_by(user_id=user_id).all()
    card_list = '<h2>Your Payment Cards:</h2>'
    for card in cards:
        card_list += (f'<p><strong>{card.card_holder}</strong> - Card Number: {card.card_number} '
                      f'- Expires: {card.expiration_date} - Billing Zip: {card.billing_zip}</p>')
    card_list += '<br><a href="/add-card">Add another card</a>'
    return card_list

if __name__ == '__main__':
    # Create tables manually before running the application.
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)
