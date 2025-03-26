from flask import Flask, request, jsonify
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

    def __repr__(self):
        return '<User %r>' % self.email

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.json.get('email')

    # Verify user identity (replace this with your actual authentication mechanism)
    # For simplicity, we'll assume the email is sufficient for now
    user = User.query.filter_by(email=email).first()

    if user:
        user.is_subscribed = False
        user.unsubscription_reason = request.json.get('reason', '')
        db.session.commit()
        return jsonify({'message': 'Unsubscribed successfully'})
    else:
        return jsonify({'error': 'User not found'}), 404

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        db.drop_all()

def test_unsubscribe(client):
    # Create a test user
    user = User(email='test@example.com', is_subscribed=True)
    db.session.add(user)
    db.session.commit()

    # Unsubscribe the user
    response = client.post('/unsubscribe', json={'email': 'test@example.com'})

    assert response.status_code == 200
    assert response.json['message'] == 'Unsubscribed successfully'

    # Verify the user's subscription status
    user = User.query.filter_by(email='test@example.com').first()
    assert not user.is_subscribed