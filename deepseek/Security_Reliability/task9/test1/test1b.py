from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize token serializer
serializer = URLSafeTimedSerializer(app.secret_key)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    is_subscribed = db.Column(db.Boolean, default=True)
    reason = db.Column(db.Text)
    updated_at = db.Column(db.DateTime)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# Helper Functions
def generate_unsubscribe_token(user_email):
    return serializer.dumps(user_email, salt='unsubscribe-salt')

def verify_unsubscribe_token(token, max_age=3600):
    try:
        email = serializer.loads(token, salt='unsubscribe-salt', max_age=max_age)
    except:
        return None
    return email

# Routes
@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    email = verify_unsubscribe_token(token)
    if not email:
        return "Invalid or expired token", 400
    
    # Check if user is logged in
    if 'user_id' not in session:
        session['unsubscribe_token'] = token
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.email != email:
        return "Unauthorized", 403
    
    return render_template('unsubscribe_form2.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            session['user_id'] = user.id
            if 'unsubscribe_token' in session:
                return redirect(url_for('unsubscribe', token=session.pop('unsubscribe_token')))
            return redirect(url_for('profile'))
        return "Invalid credentials", 401
    return render_template('login2.html')

@app.route('/process_unsubscribe', methods=['POST'])
def process_unsubscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    
    if subscription:
        subscription.is_subscribed = False
        subscription.reason = request.form.get('reason', '')
        subscription.updated_at = datetime.now()
        db.session.commit()
    
    return render_template('unsubscribe_success.html')

# Testing Endpoint
@app.route('/test_unsubscribe')
def test_unsubscribe():
    # Create test user
    test_email = "test@example.com"
    user = User.query.filter_by(email=test_email).first()
    if not user:
        user = User(email=test_email, password="test123")
        db.session.add(user)
        db.session.commit()
    
    # Create test subscription
    subscription = Subscription(user_id=user.id)
    db.session.add(subscription)
    db.session.commit()
    
    # Generate unsubscribe link
    token = generate_unsubscribe_token(test_email)
    return f"Test unsubscribe link: {url_for('unsubscribe', token=token, _external=True)}"

if __name__ == '__main__':
    app.run(debug=True)