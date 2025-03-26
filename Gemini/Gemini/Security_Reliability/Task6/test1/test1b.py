from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, validators

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
db = SQLAlchemy(app)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating', validators=[validators.DataRequired(), validators.NumberRange(min=1, max=5)])
    review_text = TextAreaField('Review', validators=[validators.DataRequired()])

@app.route('/products/<int:product_id>/review', methods=['GET', 'POST'])
def product_review(product_id):
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(product_id=product_id, user_id=current_user.id, rating=form.rating.data, review_text=form.review_text.data)
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('product_detail', product_id=product_id))
    return render_template('review_form.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)