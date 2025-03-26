from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, User, Product, Review, Purchase

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Ensure the tables are created when the app starts
with app.app_context():
    db.drop_all()
    db.create_all()

    # Insert test data
    if not User.query.first():
        user1 = User(username='testuser1', email='testuser1@example.com')
        user2 = User(username='testuser2', email='testuser2@example.com')
        user3 = User(username='testuser3', email='testuser3@example.com')

        product1 = Product(name='Test Product 1')
        product2 = Product(name='Test Product 2')

        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(product1)
        db.session.add(product2)
        db.session.commit()

        purchase1 = Purchase(user_id=user1.id, product_id=product1.id)
        purchase2 = Purchase(user_id=user2.id, product_id=product2.id)

        db.session.add(purchase1)
        db.session.add(purchase2)
        db.session.commit()

@app.route('/review/<int:product_id>', methods=['GET', 'POST'])
def review_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        review_text = request.form['review_text']
        score = request.form['score']
        
        # Verify that the user exists
        user = User.query.get(user_id)
        if not user:
            flash('User does not exist.', 'error')
            return redirect(url_for('review_product', product_id=product_id))
        
        # Verify that the user has purchased this product
        purchase = Purchase.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not purchase:
            flash('You have not purchased this product.', 'error')
            return redirect(url_for('review_product', product_id=product_id))
        
        # Validate that both review text and score are filled out
        if not review_text or not score:
            flash('Both review text and score are required.', 'error')
            return redirect(url_for('review_product', product_id=product_id))

        # Ensure the score is between 1 and 5
        try:
            score = int(score)
            if score < 1 or score > 5:
                flash('The score must be between 1 and 5.', 'error')
                return redirect(url_for('review_product', product_id=product_id))
        except ValueError:
            flash('The score must be an integer between 1 and 5.', 'error')
            return redirect(url_for('review_product', product_id=product_id))
        
        # Check if user already reviewed the product
        existing_review = Review.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing_review:
            # Update the existing review
            existing_review.review_text = review_text
            existing_review.score = score
        else:
            # Add a new review
            review = Review(user_id=user_id, product_id=product_id, review_text=review_text, score=score)
            db.session.add(review)
        
        db.session.commit()
        flash('Your review has been submitted successfully!', 'success')
        return redirect(url_for('review_success', product_id=product_id))

    return render_template('review_form.html', product=product)

@app.route('/review_success/<int:product_id>')
def review_success(product_id):
    return f"Thank you! Your review for product {product_id} has been submitted."

if __name__ == '__main__':
    app.run(debug=True)