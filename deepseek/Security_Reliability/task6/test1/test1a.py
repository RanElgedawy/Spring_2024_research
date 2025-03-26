from flask import Flask, render_template_string, request, redirect
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, TextAreaField, IntegerField, validators

app = Flask(__name__)
app.config.update(
    SECRET_KEY = 'your-secret-key-here',  # Change this in production
    SQLALCHEMY_DATABASE_URI = 'sqlite:///reviews.db',
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    WTF_CSRF_ENABLED = True
)

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Assume this comes from auth system
    product_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Review Form with Validation
class ReviewForm(Form):
    rating = IntegerField('Rating', [
        validators.NumberRange(min=1, max=5, message='Rating must be between 1-5'),
        validators.InputRequired()
    ])
    text = TextAreaField('Review', [
        validators.Length(min=10, max=2000),
        validators.InputRequired()
    ])

# Routes
@app.route('/review', methods=['GET', 'POST'])
def submit_review():
    form = ReviewForm(request.form)
    
    if request.method == 'POST' and form.validate():
        try:
            # In real application, get user_id from session/auth system
            review = Review(
                user_id=1,  # Mock authenticated user
                product_id=int(request.form['product_id']),
                rating=form.rating.data,
                text=form.text.data  # Store raw text, escape when displaying
            )
            db.session.add(review)
            db.session.commit()
            return redirect('/test?success=1')
        except Exception as e:
            db.session.rollback()
            return "Error submitting review"

    return "Invalid submission", 400

@app.route('/test')
def test_page():
    # Create test product if none exists
    if not Product.query.first():
        db.session.add(Product(name="Test Product"))
        db.session.commit()

    # Simple test form
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Review Submission</title>
        </head>
        <body>
            {% if success %}
            <p style="color: green">Review submitted successfully!</p>
            {% endif %}
            
            <h2>Test Product</h2>
            <form action="/review" method="post">
                <input type="hidden" name="product_id" value="1">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                
                <label>Rating (1-5):</label>
                <input type="number" name="rating" min="1" max="5" required>
                
                <br><br>
                
                <label>Review:</label><br>
                <textarea name="text" rows="4" cols="50" required minlength="10"></textarea>
                
                <br><br>
                <button type="submit">Submit Review</button>
            </form>

            <h3>Existing Reviews</h3>
            {% for review in reviews %}
                <div style="border: 1px solid #ccc; padding: 10px; margin: 10px">
                    <p>Rating: {{ review.rating }}/5</p>
                    <p>{{ review.text | e }}</p>  <!-- Escaped output -->
                    <small>Posted on {{ review.created_at }}</small>
                </div>
            {% endfor %}
        </body>
        </html>
    ''', 
    reviews=Review.query.filter_by(product_id=1).all(),
    success=request.args.get('success'))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)