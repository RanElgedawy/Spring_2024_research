from flask import Flask, render_template, request, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

def validate_registration_form(username, email, password):
    if not username or not email or not password:
        return False
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first() or \
                   User.query.filter_by(email=email).first()
    if existing_user:
        return False
    # Add more validation checks as needed
    return True

def validate_login_form(username_or_email, password):
    if not username_or_email or not password:
        return False
    # Check if user exists
    user = User.query.filter_by(username=username_or_email).first() or \
           User.query.filter_by(email=username_or_email).first()
    if not user:
        return False
    return True

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'] 

        if not validate_registration_form(username, email, password):
            return render_template('register.html', error='Username or email already exists.')

        # Hash password using Bcrypt
        hashed_password = bcrypt.generate_password_hash(password)
        user = User(username=username, email=email, password_hash=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'), code=302)  # Redirect to login page with success message
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f"Registration failed: {e}")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        if not validate_login_form(username_or_email, password):
            return render_template('login.html', error='Incorrect credentials.')

        user = User.query.filter_by(username=username_or_email).first() or \
               User.query.filter_by(email=username_or_email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Authenticate user and allow access to protected areas
            return render_template('dashboard.html', user=user)  # Pass the user object to the template
        else:
            return render_template('login.html', error='Incorrect credentials')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/')
def index():
    dashboard_url = url_for('dashboard')
    return f"Go to the dashboard: <a href='{dashboard_url}'>Dashboard</a>"

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)