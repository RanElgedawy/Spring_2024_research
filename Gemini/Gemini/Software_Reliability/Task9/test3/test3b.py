from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    unsubscription_reason = db.Column(db.Text)

    def __repr__(self):
        return f'<User {self.email}>'
db.drop_all()
db.create_all()

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.json['email']
    reason = request.json.get('reason')

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_subscribed = False
        user.unsubscription_reason = reason
        db.session.commit()
        return jsonify({'message': 'Unsubscribed successfully'})
    else:
        return jsonify({'error': 'User not found'}), 404