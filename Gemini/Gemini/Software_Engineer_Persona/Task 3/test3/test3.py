from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, validators
from flask_login import login_required, login_user, current_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cards.db'
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[validators.DataRequired()])
    password = PasswordField('Password', validators=[validators.DataRequired()]) 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password) 

    def get_id(self):
        return str(self.id)

    def is_active(self):
        return True
    
    @login_manager.user_loader
    def load_user(self, user_id):
        return User.query.get(int(user_id))  # Cast ID to integer in case it's a string

class PaymentCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    card_number = db.Column(db.String(16), nullable=False)
    expiration_month = db.Column(db.Integer, nullable=False)
    expiration_year = db.Column(db.Integer, nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    name_on_card = db.Column(db.String(100), nullable=False)
    billing_zip = db.Column(db.String(10), nullable=False)

class AddCardForm(FlaskForm):
    card_number = StringField('Card Number', validators=[validators.DataRequired(), validators.Length(16)])
    cvv = StringField('CVV/CVV', validators=[validators.DataRequired(), validators.Length(3)])
    expiration_month = SelectField('Expiration Month', choices=[(month, str(month)) for month in range(1, 13)], validators=[validators.DataRequired()])
    expiration_year = SelectField('Expiration Year', choices=[(year, str(year)) for year in range(datetime.now().year, datetime.now().year + 10)], validators=[validators.DataRequired()])
    name_on_card = StringField('Name on Card', validators=[validators.DataRequired()])
    billing_zip = StringField('Billing ZIP Code', validators=[validators.DataRequired(), validators.Length(5)])

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first() 

            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('add_card')) 
  # Redirect to add-card after successful login
            else:
                flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/add-card', methods=['GET', 'POST'])
@login_required
def add_card():
    form = AddCardForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Card data is valid, create a new PaymentCard instance and save it to the database
            new_card = PaymentCard(
                user_id=current_user.id,
                card_number=form.card_number.data,
                cvv=form.cvv.data,
                expiration_month=form.expiration_month.data,
                expiration_year=form.expiration_year.data,
                name_on_card=form.name_on_card.data,
                billing_zip=form.billing_zip.data
            )
            db.session.add(new_card)
            db.session.commit()

            # Redirect to user's account page or another appropriate page
            return redirect(url_for('account'))
        else:
            # Form validation failed, render the form with errors
            return render_template('add_card.html', form=form)

    return render_template('add_card.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Insert test user data (replace with your desired password)
        test_user = User(username='test_user', password=generate_password_hash('test_password'))
        db.session.add(test_user)
        db.session.commit()

    app.run(debug=True)