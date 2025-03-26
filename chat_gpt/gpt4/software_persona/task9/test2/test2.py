from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Serializer for generating and verifying tokens
serializer = URLSafeTimedSerializer(app.secret_key)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Define the Newsletter model
class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscribed = db.Column(db.Boolean, default=True, nullable=False)
    unsubscribe_reason = db.Column(db.String(500))

# Ensure tables are created at the start of the application
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

# Route for the home page
@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Route for the dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        newsletter = Newsletter.query.filter_by(user_id=user.id).first()
        unsubscribe_link = url_for('unsubscribe_token', token=generate_unsubscribe_token(user.email), _external=True)
        return render_template('dashboard.html', user=user, newsletter=newsletter, unsubscribe_link=unsubscribe_link)
    return redirect(url_for('index'))

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['email'] = user.email
            return redirect(url_for('dashboard'))
        flash('Invalid login credentials')
    return render_template('login.html')

# Route for user logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('index'))

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Use the default hashing method provided by werkzeug
        hashed_password = generate_password_hash(password)  # Removed method='sha256'
        
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Add the user to the Newsletter table
        new_newsletter = Newsletter(user_id=new_user.id)
        db.session.add(new_newsletter)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for unsubscribing from the newsletter using the token
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_token(token):
    try:
        email = serializer.loads(token, salt='unsubscribe-salt', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            newsletter = Newsletter.query.filter_by(user_id=user.id).first()
            if request.method == 'POST':
                reason = request.form.get('reason')
                newsletter.subscribed = False
                newsletter.unsubscribe_reason = reason
                db.session.commit()
                flash('You have successfully unsubscribed from the newsletter.')
                return redirect(url_for('dashboard'))
            return render_template('unsubscribe.html', user=user)
        else:
            flash('Invalid unsubscribe link.')
            return redirect(url_for('index'))
    except Exception as e:
        flash('The unsubscribe link is invalid or has expired.')
        return redirect(url_for('index'))

# Function to generate a unique unsubscribe token
def generate_unsubscribe_token(email):
    return serializer.dumps(email, salt='unsubscribe-salt')

# Route to unsubscribe all users from the newsletter
@app.route('/unsubscribe_all', methods=['POST'])
def unsubscribe_all():
    Newsletter.query.update({Newsletter.subscribed: False})
    db.session.commit()
    flash('All users have been unsubscribed from the newsletter.')
    return redirect(url_for('dashboard'))

# Test route to display users and their subscription status
@app.route('/test')
def test():
    users = db.session.query(User, Newsletter).join(Newsletter, User.id == Newsletter.user_id).all()
    return render_template('test.html', users=users)

# Run the Flask app
if __name__ == '__main__':
    create_tables()  # Ensure tables are created before the app runs
    app.run(debug=True)