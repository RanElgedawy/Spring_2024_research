from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed = db.Column(db.Boolean, default=True)
    unsubscription_reason = db.Column(db.Text)

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form['email']  # Assuming email is sent from frontend
    reason = request.form.get('reason')

    user = User.query.filter_by(email=email).first()
    if user:
        user.subscribed = False
        user.unsubscription_reason = reason
        db.session.commit()
        # Add a success message or redirect to a confirmation page
        return 'Unsubscribed successfully!'
    else:
        # Handle the case where the user is not found
        return 'User not found.', 404

url = 'http://127.0.0.1:5000/unsubscribe'  # Replace with your app's URL
data = {'email': 'user@example.com', 'reason': 'Too many emails'}
response = requests.post(url, data=data)
print(response.text)