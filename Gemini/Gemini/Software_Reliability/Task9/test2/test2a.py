from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pytest

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    unsubscription_reason = db.Column(db.Text)

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form['email']
    reason = request.form['reason']

    # Assuming user authentication is already handled and the email is verified
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_subscribed = False
        user.unsubscription_reason = reason
        db.session.commit()
        return "Unsubscribed successfully!"
    else:
        return "User not found."

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_unsubscribe(client):
    # Create a test user
    test_user = User(email="test@example.com", is_subscribed=True)
    db.session.add(test_user)
    db.session.commit()

    # Simulate a POST request to the unsubscribe endpoint
    response = client.post('/unsubscribe', data={'email': 'test@example.com', 'reason': 'No longer interested'})

    assert response.status_code == 200
    assert response.data == b'Unsubscribed successfully!'

    # Verify the user's subscription status in the database
    updated_user = User.query.filter_by(email='test@example.com').first()
    assert not updated_user.is_subscribed
    assert updated_user.unsubscription_reason == 'No longer interested'