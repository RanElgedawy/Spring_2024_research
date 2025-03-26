from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
db = SQLAlchemy(app)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    score = db.Column(db.Integer)

    def __repr__(self):
        return f"<Review {self.id}>"

@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = 1  # Replace with actual user ID
    product_id = 2  # Replace with actual product ID
    text = request.form['review_text']
    score = int(request.form['review_score'])

    review = Review(user_id=user_id, product_id=product_id, text=text, score=score)
    db.session.add(review)
    db.session.commit()

    return redirect(url_for('product_page'))  # Redirect to product page after adding review

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)