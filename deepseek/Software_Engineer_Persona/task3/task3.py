# backend.py
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import secrets
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payment_cards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    expiration = db.Column(db.String(5), nullable=False)  # MM/YY format
    cardholder = db.Column(db.String(100), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    # Added billing zip code
    billing_zip = db.Column(db.String(10), nullable=False)  # Allow for 5-digit or 9-digit formats

def validate_expiration(exp_str):
    """Validate expiration date in MM/YY format"""
    if not re.match(r'^\d{2}/\d{2}$', exp_str):
        return False, "Invalid format. Use MM/YY"
    
    month, year = exp_str.split('/')
    try:
        month_num = int(month)
        year_num = int(year)
    except ValueError:
        return False, "Invalid numbers"
    
    # Validate month
    if not (1 <= month_num <= 12):
        return False, "Invalid month"
    
    # Validate not expired
    current_year = datetime.now().year % 100  # Get last two digits
    current_month = datetime.now().month
    
    # Convert to full year (assuming 20YY format)
    full_year = 2000 + year_num
    
    # Compare dates
    if (full_year < datetime.now().year) or \
       (full_year == datetime.now().year and month_num < datetime.now().month):
        return False, "Card has expired"
    
    return True, ""

# Replace before_first_request with explicit initialization
def initialize_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

# Create CLI command to initialize database
@app.cli.command("create-tables")
def create_tables():
    """Create database tables"""
    db.create_all()
    print("Tables created successfully")

# Simple mock authentication system
@app.route('/login_test_user')
def login_test_user():
    # Create test user if not exists
    if not User.query.filter_by(username='testuser').first():
        test_user = User(username='testuser', password='testpass')
        db.session.add(test_user)
        db.session.commit()
    
    session['user_id'] = User.query.filter_by(username='testuser').first().id
    return 'Logged in as test user. <a href="/add_card">Add Card</a>'

@app.route('/add_card')
def add_card_form():
    if 'user_id' not in session:
        return 'Please login first'
    return render_template('add_card.html')

@app.route('/api/cards', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.json
    
    # Validate required fields
    required_fields = ['card_number', 'expiration', 'cvv', 'cardholder', 'billing_zip']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate expiration date
    is_valid, message = validate_expiration(data['expiration'])
    if not is_valid:
        return jsonify({'error': f'Invalid expiration: {message}'}), 400
    
    new_card = PaymentCard(
        user_id=session['user_id'],
        card_number=data['card_number'],
        expiration=data['expiration'],
        cardholder=data['cardholder'],
        cvv=data['cvv'],
        billing_zip=data['billing_zip']  # Added zip code
    )
    
    db.session.add(new_card)
    db.session.commit()
    
    return jsonify({'message': 'Card added successfully'}), 201

@app.route('/api/cards')
def get_cards():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    cards = PaymentCard.query.filter_by(user_id=session['user_id']).all()
    return jsonify([{
        'card_number': card.card_number,
        'expiration': card.expiration,
        'cardholder': card.cardholder
    } for card in cards])

if __name__ == '__main__':
    # Create tables when running the app directly
    with app.app_context():
        db.create_all()
    app.run(debug=True)