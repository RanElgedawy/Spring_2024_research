from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'

mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Serializer for generating tokens
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    subscribed = db.Column(db.Boolean, default=True)  # Subscription status

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Check email and password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/unsubscribe')
@login_required
def unsubscribe():
    token = s.dumps(current_user.email, salt='unsubscribe')
    msg = Message('Unsubscribe from Newsletter', sender='noreply@demo.com', recipients=[current_user.email])
    link = url_for('unsubscribe_token', token=token, _external=True)
    msg.body = f'Please click the link to unsubscribe: {link}'
    mail.send(msg)
    flash('An email has been sent to unsubscribe you from the newsletter.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_token(token):
    try:
        email = s.loads(token, salt='unsubscribe', max_age=3600)  # Token valid for 1 hour
    except (SignatureExpired, BadTimeSignature):
        flash('The unsubscribe link is invalid or has expired.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.filter_by(email=email).first_or_404()
    
    if request.method == 'POST':
        # Update user's subscription preference
        user.subscribed = False
        db.session.commit()
        flash('You have been unsubscribed from the newsletter.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('unsubscribe.html', user=user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Database initialization
@app.before_first_request
def create_tables():
    db.create_all()

# Sample route for registration (for testing)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='sha256')
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
