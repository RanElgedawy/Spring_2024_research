from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class ReviewForm(FlaskForm):
    text = StringField('Review Text', validators=[DataRequired(), Length(min=1, max=500)])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')

with app.app_context():
    db.drop_all()
    db.create_all()
    test_product = Product(name="Test Product", description="This is a test product for review testing")
    db.session.add(test_product)
    db.session.commit()

@app.route('/products/<int:product_id>/reviews', methods=['GET', 'POST'])
def product_reviews(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return "Product not found", 404

    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            text=form.text.data,
            rating=form.rating.data,
            product_id=product_id,
            user_id=current_user.id  # Assuming a logged-in user
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('product_reviews', product_id=product_id))

    reviews = Review.query.filter_by(product_id=product_id).all()
    return render_template('product_reviews.html', product=product, reviews=reviews, form=form)

if __name__ == '__main__':
    app.run(debug=True)