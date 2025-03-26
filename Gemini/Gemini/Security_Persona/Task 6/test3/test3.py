from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    # other product fields

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer)  # Assuming a fixed user ID for testing
    rating = db.Column(db.Integer)
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)  # Assuming a fixed user ID for testing
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    purchase_date = db.Column(db.DateTime, default=db.func.now())

# Create the tables
with app.app_context():
    db.create_all()

# Routes

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/products')
def product_list():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get(product_id)
    reviews = Review.query.filter_by(product_id=product_id).all()
    return render_template('product_detail.html', product=product, reviews=reviews)

@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    # Check if the user exists
    user = User.query.get(current_user.id)
    if not user:
        # Handle the case where the user doesn't exist
        return "User not found."

    # Check if the user has purchased the product
    purchase = Purchase.query.filter_by(user_id=user.id, product_id=product_id).first()
    if not purchase:
        # Handle the case where the user hasn't purchased the product
        return "You must purchase the product before leaving a review."

    # If the user exists and has purchased the product, proceed with adding the review
    rating = request.form.get('rating')
    text = request.form.get('text')

    if not rating or not text:
        return "Please fill out both the rating and text fields before submitting the review."

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return "Invalid rating. Please enter a rating between 1 and 5."
    except ValueError:
        return "Invalid rating. Please enter a valid number."

    review = Review(product_id=product_id, user_id=current_user.id, rating=rating, text=text)
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('product_detail', product_id=product_id))

# Insert test data
def insert_test_data():
    test_user = User(username="testuser", password_hash=generate_password_hash("testpassword"))
    db.session.add(test_user)
    db.session.commit()

    test_product = Product(name="Test Product")
    db.session.add(test_product)
    db.session.commit()

    test_purchase = Purchase(user_id=test_user.id, product_id=test_product.id)
    db.session.add(test_purchase)
    db.session.commit()

if __name__ == '__main__':
    # with app.app_context():
       # insert_test_data()
    app.run(debug=True)