from flask import Flask, request, jsonify, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed = db.Column(db.Boolean, default=True)
    unsubscription_reason = db.Column(db.Text)
    unsubscribe_token = db.Column(db.String(128), unique=True)

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscribed = db.Column(db.Boolean, default=True)

@app.route('/unsubscribe/<token>', methods=['GET'])
def unsubscribe_link(token):
    user = User.query.filter_by(unsubscribe_token=token).first()
    if user:
        user.subscribed = False
        db.session.commit()

        # Update the Newsletter table if all users are unsubscribed
        newsletter_status = Newsletter.query.first()
        newsletter_status.subscribed = User.query.filter_by(subscribed=True).count() != 0
        db.session.commit()

        return jsonify({'message': 'Unsubscribed successfully'})
    else:
        return jsonify({'error': 'Invalid token'})

@app.route('/generate_unsubscribe_link', methods=['POST'])
def generate_unsubscribe_link():
    data = request.get_json()
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if user:
        user.unsubscribe_token = str(uuid.uuid4())
        db.session.commit()

        unsubscribe_link = url_for('unsubscribe_link', token=user.unsubscribe_token)
        return jsonify({'unsubscribe_link': unsubscribe_link})
    else:
        return jsonify({'error': 'User not found'})

@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    try:
        # Update the newsletter table (assuming a Newsletter model)
        Newsletter.query.update({Newsletter.subscribed: False})
        db.session.commit()
        return jsonify({'message': 'All users unsubscribed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/newsletter_status', methods=['GET'])
def newsletter_status():
    # Retrieve the newsletter status (assuming a Newsletter model)
    newsletter_status = Newsletter.query.first().subscribed
    return jsonify({'status': newsletter_status})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        test_user = User(email="test@example.com")
        db.session.add(test_user)
        db.session.commit()

        # Create a newsletter status
        newsletter_status = Newsletter()
        db.session.add(newsletter_status)
        db.session.commit()
    
    app.run(debug=True)