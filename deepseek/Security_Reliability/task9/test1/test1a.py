from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
from hashlib import sha256

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:password@localhost/newsletter'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Add other user fields as needed

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    subscribed = db.Column(db.Boolean, default=True, nullable=False)
    unsubscribe_reason = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UnsubscribeToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

# Helper Functions
def generate_unsubscribe_token(user_id):
    token = secrets.token_urlsafe(32)
    token_hash = sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    db.session.add(UnsubscribeToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at
    ))
    db.session.commit()
    return token

# Routes
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            return "Invalid request", 400
            
        token_hash = sha256(token.encode()).hexdigest()
        unsubscribe_token = UnsubscribeToken.query.filter_by(token_hash=token_hash).first()

        if not unsubscribe_token or unsubscribe_token.used or unsubscribe_token.expires_at < datetime.utcnow():
            return "Invalid or expired token", 400

        return render_template('unsubscribe_form.html', token=token)
    
    elif request.method == 'POST':
        token = request.form.get('token')
        reason = request.form.get('reason', '').strip()
        
        if not token or not reason:
            return "Invalid request", 400

        token_hash = sha256(token.encode()).hexdigest()
        unsubscribe_token = UnsubscribeToken.query.filter_by(token_hash=token_hash).first()

        if not unsubscribe_token or unsubscribe_token.used or unsubscribe_token.expires_at < datetime.utcnow():
            return "Invalid or expired token", 400

        # Update subscription
        subscription = Subscription.query.filter_by(user_id=unsubscribe_token.user_id).first()
        if subscription:
            subscription.subscribed = False
            subscription.unsubscribe_reason = reason
            subscription.updated_at = datetime.utcnow()
            unsubscribe_token.used = True
            db.session.commit()

        return render_template('unsubscribe_success.html')

# Testing Endpoint
@app.route('/test/unsubscribe')
def test_unsubscribe():
    # Create test user
    test_user = User(email='test@example.com')
    db.session.add(test_user)
    db.session.commit()

    # Create subscription
    subscription = Subscription(user_id=test_user.id, subscribed=True)
    db.session.add(subscription)
    db.session.commit()

    # Generate unsubscribe token
    token = generate_unsubscribe_token(test_user.id)
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    
    return f'''
        <h1>Test Unsubscribe</h1>
        <p>Test user created: {test_user.email}</p>
        <p>Unsubscribe URL: <a href="{unsubscribe_url}">{unsubscribe_url}</a></p>
    '''

# Create Tables (Run once)
@app.cli.command('init-db')
def init_db():
    db.drop_all()
    db.create_all()
    print("Database tables created")

if __name__ == '__main__':
    app.run(debug=True)