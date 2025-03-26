from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import secrets
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'
db = SQLAlchemy(app)

class User(db.Model):
    # ... your existing User model
    subscriptions = db.relationship('Subscription', backref='user')

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(255), nullable=False)
    subscribed = db.Column(db.Boolean, default=True)
    unsubscribe_token = db.Column(db.String(255), unique=True)
    unsubscribe_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# ... your existing routes

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    subscription = Subscription.query.filter_by(unsubscribe_token=token).first()
    if not subscription:
        flash('Invalid unsubscribe token.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        subscription.subscribed = False
        subscription.unsubscribe_reason = request.form['unsubscribe_reason']
        db.session.commit()
        flash('Unsubscribed successfully.')
        return redirect(url_for('home'))

    return render_template('unsubscribe.html', subscription=subscription)

@app.route('/send_unsubscribe_link', methods=['POST'])
def send_unsubscribe_link():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    if user:
        subscription = user.subscriptions.filter_by(email=email).first()
        if not subscription:
            subscription = Subscription(user=user, email=email)
            db.session.add(subscription)

        subscription.unsubscribe_token = secrets.token_urlsafe(32)
        db.session.commit()

        # Send unsubscribe email
        # ... your email sending logic

        flash('Unsubscribe link sent to your email.')
    else:
        flash('User not found.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)