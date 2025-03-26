from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)

# JWT secret key
JWT_SECRET = 'your_jwt_secret_key'


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    unsubscribe_reason = db.Column(db.String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Routes and logic

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You must be logged in.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    
    return render_template('profile.html', user=user)


@app.route('/send_unsubscribe_link', methods=['POST'])
def send_unsubscribe_link():
    if 'user_id' not in session:
        flash('You must be logged in to unsubscribe.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    
    if user:
        # Generate JWT token with a 1-hour expiration
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            JWT_SECRET,
            algorithm='HS256'
        )
        
        # Generate the unsubscribe link
        unsubscribe_link = url_for('unsubscribe', token=token, _external=True)

        # Simulate sending the email by printing the unsubscribe link to the console
        print(f'Unsubscribe link for {user.email}: {unsubscribe_link}')

        flash('An unsubscribe link has been generated and "sent" (check the console).', 'success')
        return redirect(url_for('profile'))

    flash('Error: Unable to generate unsubscribe link.', 'error')
    return redirect(url_for('profile'))


@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    try:
        # Decode the JWT token
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = User.query.get(data['user_id'])

        if not user or 'user_id' not in session or session['user_id'] != user.id:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('login'))

        if request.method == 'POST':
            reason = request.form.get('reason')
            user.is_subscribed = False
            user.unsubscribe_reason = reason
            db.session.commit()

            flash('You have successfully unsubscribed from the newsletter.', 'success')
            return redirect(url_for('profile'))

        return render_template('unsubscribe.html', user=user)
    
    except jwt.ExpiredSignatureError:
        flash('The unsubscribe link has expired. Please request a new one.', 'error')
        return redirect(url_for('profile'))
    except jwt.InvalidTokenError:
        flash('Invalid token. Please try again.', 'error')
        return redirect(url_for('profile'))


# Unsubscribe All Users
@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    if 'user_id' not in session:
        flash('You must be logged in to perform this action.', 'error')
        return redirect(url_for('login'))

    # Unsubscribe all users by setting their subscription status to False in the User table
    User.query.update({User.is_subscribed: False})
    db.session.commit()

    flash('All users have been unsubscribed from the newsletter.', 'success')
    return redirect(url_for('profile'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id

            flash('Logged in successfully.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid credentials.', 'error')

    return render_template('login.html')


# Automatically create database tables if they don't exist and insert test data
with app.app_context():
    db.create_all()

    # Insert test data if the database is empty
    if User.query.count() == 0:
        # Create test users
        user1 = User(email="testuser1@example.com")
        user1.set_password("password1")
        user2 = User(email="testuser2@example.com")
        user2.set_password("password2")
        user3 = User(email="testuser3@example.com")
        user3.set_password("password3")

        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()

        print("Test users created.")


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)