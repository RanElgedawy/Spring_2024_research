from flask import Flask, request, render_template, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed = db.Column(db.Boolean, default=True, nullable=False)
    unsubscribe_feedback = db.Column(db.Text)

# Create tables if they don't exist
with app.app_context():
    db.drop_all()
    db.create_all()

# JWT token generation
def generate_unsubscribe_token(user_id):
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {
        'user_id': user_id,
        'exp': expiration
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# JWT token verification
def verify_unsubscribe_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

# Unsubscribe routes
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    user_id = verify_unsubscribe_token(token)
    if not user_id:
        abort(401, "Invalid or expired unsubscribe link")
    
    user = User.query.get(user_id)
    if not user:
        abort(404, "User not found")

    if request.method == 'POST':
        # Update subscription status
        user.subscribed = False
        user.unsubscribe_feedback = request.form.get('feedback', '')
        db.session.commit()
        return render_template('unsubscribe_success.html')

    return render_template('unsubscribe_form.html', email=user.email)

# Test route to generate unsubscribe link
@app.route('/test/unsubscribe-link/<int:user_id>')
def test_unsubscribe_link(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    
    token = generate_unsubscribe_token(user_id)
    unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
    return f"Test unsubscribe link for {user.email}: {unsubscribe_url}"

if __name__ == '__main__':
    with app.app_context():
        test_user = User(email='test@example.com', subscribed=True)
        db.session.add(test_user)
        db.session.commit()
    app.run(debug=True)