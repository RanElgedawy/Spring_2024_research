# backend.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from wtforms import Form, validators, FloatField, StringField
import bleach

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'your-secret-key-here',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///reviews.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Database models
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Assume comes from auth system
    product_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review_text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<Review {self.id}>'

# Validation form
class ReviewForm(Form):
    rating = FloatField('Rating', [
        validators.NumberRange(min=1, max=5, message='Rating must be between 1-5'),
        validators.InputRequired()
    ])
    review_text = StringField('Review Text', [
        validators.Length(min=1, max=500),
        validators.InputRequired()
    ])

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/submit-review', methods=['POST'])
@csrf.protect
def submit_review():
    try:
        form = ReviewForm(request.form)
        
        if not form.validate():
            return jsonify({"error": form.errors}), 400

        # Sanitize input
        clean_review = bleach.clean(
            form.review_text.data,
            tags=['br', 'em', 'strong', 'p'],
            attributes={'*': ['class']},
            strip=True
        )

        # Assume user_id comes from session/auth system
        # In real implementation, get from authenticated user
        new_review = Review(
            user_id=1,  # Replace with actual user ID from session
            product_id=int(request.args.get('product_id')),
            rating=form.rating.data,
            review_text=clean_review
        )

        db.session.add(new_review)
        db.session.commit()

        return jsonify({
            "message": "Review submitted successfully",
            "review_id": new_review.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)