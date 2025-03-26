from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET'] = 'jwt_secret_key_here'  # Replace with a strong JWT secret
app.config['JWT_EXPIRATION'] = timedelta(hours=24)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    last_unsubscribed = db.Column(db.DateTime)

class UnsubscribeReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def generate_unsubscribe_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + app.config['JWT_EXPIRATION']
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def verify_unsubscribe_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# Routes
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    # Verify token
    user_id = verify_unsubscribe_token(token)
    if not user_id:
        return "Invalid or expired unsubscribe link", 400

    # Check if user is logged in
    if 'user_id' not in session or session['user_id'] != user_id:
        session['unsubscribe_token'] = token  # Store token for after login
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        # Update subscription status
        user.is_subscribed = False
        user.last_unsubscribed = datetime.utcnow()

        # Save reason
        reason = request.form.get('reason', 'No reason provided')
        db.session.add(UnsubscribeReason(user_id=user_id, reason=reason))
        db.session.commit()

        return render_template('unsubscribe_success.html')

    return render_template('unsubscribe_form2.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Implement your actual login logic here
    # For demo purposes, we'll automatically log in the test user
    if request.method == 'POST':
        # Normally you'd verify credentials here
        session['user_id'] = request.form.get('user_id')
        if 'unsubscribe_token' in session:
            token = session.pop('unsubscribe_token')
            return redirect(url_for('unsubscribe', token=token))
        return redirect(url_for('index'))
    return render_template('login.html')

# Test Routes
@app.route('/test/send-unsubscribe-email/<user_id>')
def test_send_unsubscribe_email(user_id):
    user = User.query.get(user_id)
    if not user:
        user = User(id=user_id, email='test@example.com')
        db.session.add(user)
        db.session.commit()

    token = generate_unsubscribe_token(user_id)
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    print(f"Test Unsubscribe URL: {unsubscribe_url}")  # In production, send this via email
    return f"Test unsubscribe email sent. URL: {unsubscribe_url}"

@app.route('/test/user-status/<user_id>')
def test_user_status(user_id):
    user = User.query.get(user_id)
    return {
        'is_subscribed': user.is_subscribed if user else None,
        'last_unsubscribed': user.last_unsubscribed if user else None
    }

# Templates (create these in templates/ directory)
# unsubscribe_form.html, unsubscribe_success.html, login.html

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)