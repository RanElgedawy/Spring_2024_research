from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import os

app = Flask(__name__)
# Note: In a production app, use a strong secret key and store it securely.
app.config['SECRET_KEY'] = 'this-should-be-a-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define our models: one for products and one for reviews.
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

# Create tables and a sample product for testing.
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()
    if not Product.query.first():
        sample_product = Product(name="Test Product")
        db.session.add(sample_product)
        db.session.commit()

# Define a form for review submission with CSRF protection.
class ReviewForm(FlaskForm):
    text = TextAreaField('Review', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')

# Inline HTML templates for a self-contained example.
index_template = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Products</title>
</head>
<body>
  <h1>Products</h1>
  <ul>
    {% for product in products %}
      <li><a href="{{ url_for('product_detail', product_id=product.id) }}">{{ product.name }}</a></li>
    {% endfor %}
  </ul>
</body>
</html>
'''

product_detail_template = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ product.name }}</title>
</head>
<body>
  <h1>{{ product.name }}</h1>
  <p><a href="{{ url_for('add_review', product_id=product.id) }}">Add Review</a></p>
  <h2>Reviews</h2>
  <ul>
    {% for review in reviews %}
      <li>
        <strong>Rating: {{ review.rating }}</strong><br>
        {{ review.text }}
      </li>
    {% else %}
      <li>No reviews yet.</li>
    {% endfor %}
  </ul>
  <p><a href="{{ url_for('index') }}">Back to Products</a></p>
</body>
</html>
'''

add_review_template = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Add Review for {{ product.name }}</title>
</head>
<body>
  <h1>Add Review for {{ product.name }}</h1>
  <form method="post">
    {{ form.hidden_tag() }}
    <p>
      {{ form.text.label }}<br>
      {{ form.text(rows=5, cols=40) }}
    </p>
    <p>
      {{ form.rating.label }}<br>
      {{ form.rating() }}
    </p>
    <p>{{ form.submit() }}</p>
  </form>
  <p><a href="{{ url_for('product_detail', product_id=product.id) }}">Back to Product</a></p>
</body>
</html>
'''

@app.route('/')
def index():
    products = Product.query.all()
    return render_template_string(index_template, products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).all()
    return render_template_string(product_detail_template, product=product, reviews=reviews)

@app.route('/product/<int:product_id>/review', methods=['GET', 'POST'])
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    if form.validate_on_submit():
        # Creating a new review; SQLAlchemy's parameterized queries protect against SQL injection.
        new_review = Review(product_id=product_id, text=form.text.data, rating=form.rating.data)
        db.session.add(new_review)
        db.session.commit()
        flash("Review submitted successfully!", "success")
        return redirect(url_for('product_detail', product_id=product_id))
    return render_template_string(add_review_template, form=form, product=product)

if __name__ == '__main__':
    # Run the app in debug mode for testing.
    app.run(debug=True)
