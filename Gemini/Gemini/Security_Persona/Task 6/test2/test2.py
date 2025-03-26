from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = 'your_unique_secret_key'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user_id, user[1], user[2])
    return None

@app.route('/')
def home():
    return "Welcome to the home page!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 


        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()

        if user_data:
            user = User(user_data[0], user_data[1], user_data[2])
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password')
        else:
            flash('Invalid username or password')

    return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/products/<int:product_id>/review', methods=['GET', 'POST'])
def product_review(product_id):
    if request.method == 'POST':
        rating = request.form['rating']
        review_text = request.form['review_text']

        # Validate input
        if not rating or not review_text:
            flash("Please fill out both the review text and rating.")
            return render_template('product_review.html', product_id=product_id)

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            flash("The rating must be between 1 and 5.")
            return render_template('product_review.html', product_id=product_id)

        if current_user.is_authenticated:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the user has purchased the product
            cursor.execute("SELECT 1 FROM purchases WHERE user_id = ? AND product_id = ?",
                           (current_user.id, product_id))
            result = cursor.fetchone()

            if result:
                # User has purchased the product, proceed with review
                cursor.execute("INSERT INTO reviews (product_id, user_id, rating, review_text) VALUES (?, ?, ?, ?)",
                               (product_id, current_user.id, rating, review_text))
                conn.commit()

                flash("Your review has been submitted.")
                return redirect(url_for('product_details', product_id=product_id))
            else:
                flash("You must have purchased this product to leave a review.")
        else:
            flash("You must be logged in to leave a review.")
            return redirect(url_for('login'))

    return render_template('product_review.html', product_id=product_id)

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS purchases")
    cursor.execute("DROP TABLE IF EXISTS reviews")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def insert_test_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert a test user with hashed password
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                   ("testuser", generate_password_hash("testpassword")))

    # Insert a test product
    cursor.execute("INSERT INTO products (name, price) VALUES ('Test Product', 19.99)")

    # Insert a test purchase
    cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 1)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    insert_test_data()
    app.run(debug=True)