from flask import Flask, redirect, url_for, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import secrets
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET'] = secrets.token_hex(32)
app.config['JWT_EXPIRATION'] = 3600  # 1 hour expiration

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_subscribed = db.Column(db.Boolean, default=True)

class UnsubscribeReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

# JWT Token Handling
def create_unsubscribe_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_EXPIRATION'])
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def validate_unsubscribe_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# Routes
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    token = request.args.get('token')
    
    if not token:
        return "Invalid unsubscribe link", 400
        
    user_id = validate_unsubscribe_token(token)
    if not user_id:
        return "Invalid or expired unsubscribe link", 400
    
    # Check if user is logged in
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('login', next=request.url))
    
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    
    if request.method == 'POST':
        reason = request.form.get('reason', '')
        
        # Update subscription status
        user.is_subscribed = False
        db.session.add(user)
        
        # Record reason
        if reason:
            unsubscribe_reason = UnsubscribeReason(
                user_id=user_id,
                reason=reason
            )
            db.session.add(unsubscribe_reason)
        
        db.session.commit()
        return "You have been unsubscribed successfully"
    
    return render_template('unsubscribe.html')

# Mock authentication routes for testing
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # In real implementation, verify password hash
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            return redirect(request.args.get('next') or url_for('index'))
        return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Test endpoint
@app.route('/test')
def test_setup():
    # Create test user
    test_email = "test@example.com"
    user = User.query.filter_by(email=test_email).first()
    if not user:
        user = User(
            email=test_email,
            password_hash=generate_password_hash("testpassword"),
            is_subscribed=True
        )
        db.session.add(user)
        db.session.commit()
    
    # Generate unsubscribe link
    token = create_unsubscribe_token(user.id)
    return f'''
        <h1>Test Setup Complete</h1>
        <p>Test user created: {test_email}</p>
        <p><a href="{url_for('login')}">Login</a></p>
        <p>Unsubscribe link: <a href="{url_for('unsubscribe', token=token)}">{url_for('unsubscribe', token=token)}</a></p>
    '''

@app.route('/')
def index():
    return "E-commerce Newsletter Management"

if __name__ == '__main__':
    app.run(debug=True)