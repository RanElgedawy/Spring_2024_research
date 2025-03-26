from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
db = SQLAlchemy(app)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Review text="{self.text}", rating={self.rating}>'

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/reviews', methods=['POST'])
def create_review():
    data = request.get_json()
    review = Review(text=data['text'], rating=data['rating'], user_id=data['userId'])
    db.session.add(review)
    db.session.commit()
    return jsonify({'message': 'Review created successfully'})

if __name__ == '__main__':
    app.run(debug=True)