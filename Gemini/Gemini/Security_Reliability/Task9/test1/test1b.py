import smtplib
from flask import Flask, request, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_subscriptions.db'
db = SQLAlchemy(app)

class UserSubscription(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    subscribed = db.Column(db.Boolean, default=True)
    unsubscribe_reason = db.Column(db.String(100))

# ... (your login and authentication code)

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    user = User.query.filter_by(token=token).first()
    if not user or not user.is_authenticated:
        return redirect(url_for('login'))

    # ... (prompt for reason and store in database)

    user.subscription.subscribed = False
    db.session.commit()

    # ... (send confirmation email)

    return render_template('unsubscribe_confirmation.html')