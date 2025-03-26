from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import secrets
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'  # Replace with your DB URI
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    unsubscribe_reason = db.Column(db.Text)

class UnsubscribeToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# ... (other routes and functions)

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    # Generate a unique token
    token = secrets.token_urlsafe(32)

    # Create a token record
    unsubscribe_token = UnsubscribeToken(token=token, user_id=current_user.id)
    db.session.add(unsubscribe_token)
    db.session.commit()

    # Send an email with the unsubscribe link
    # ... (use your email sending library)

    return render_template('unsubscribe_confirmation.html')

@app.route('/unsubscribe/<token>')
def unsubscribe_confirm(token):
    unsubscribe_token = UnsubscribeToken.query.filter_by(token=token).first()
    if not unsubscribe_token:
        return "Invalid unsubscribe link"

    user = User.query.get(unsubscribe_token.user_id)
    if not user:
        return "User not found"

    # Ask for unsubscribe reason
    # ... (render a form or use a modal)

    user.is_subscribed = False
    db.session.commit()

    return "You have successfully unsubscribed."