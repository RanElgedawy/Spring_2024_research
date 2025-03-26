from flask import Flask, render_template_string, redirect, url_for, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, validators
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_subscribed = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[validators.DataRequired()])

class BulkUnsubscribeForm(FlaskForm):
    admin_password = PasswordField('Admin Password', validators=[validators.DataRequired()])

# Create tables and initial users
with app.app_context():
    db.drop_all()
    db.create_all()
    # Create admin user
    if not User.query.filter_by(email='admin@example.com').first():
        admin_user = User(email='admin@example.com', is_admin=True)
        admin_user.set_password('adminpassword')
        db.session.add(admin_user)
    # Create regular user
    if not User.query.filter_by(email='user@example.com').first():
        regular_user = User(email='user@example.com')
        regular_user.set_password('userpassword')
        db.session.add(regular_user)
    db.session.commit()

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_profile'))
    return render_template_string('''
        <h1>Welcome</h1>
        <p><a href="{{ url_for('login') }}">Login</a></p>
        <p><a href="{{ url_for('admin_dashboard') }}">Admin Login</a></p>
    ''')

# Update login route template rendering
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_profile'))
        flash('Invalid email or password', 'danger')
    
    return render_template_string('''
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <h2>Login</h2>
        <form method="POST">
            {{ form.hidden_tag() }}  <!-- Changed from csrf_token -->
            {{ form.email.label }} {{ form.email() }}<br>
            {{ form.password.label }} {{ form.password() }}<br>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="{{ url_for('home') }}">Contact administrator</a></p>
    ''', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    return render_template_string('''
        <h1>Admin Dashboard</h1>
        <p>Welcome {{ user.email }}</p>
        <p><a href="{{ url_for('admin_unsubscribe_all') }}">Bulk Unsubscribe All Users</a></p>
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
    ''', user=user)

@app.route('/admin/unsubscribe-all', methods=['GET', 'POST'])
def admin_unsubscribe_all():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    form = BulkUnsubscribeForm()
    if form.validate_on_submit():
        if user.check_password(form.admin_password.data):
            User.query.update({User.is_subscribed: False})
            db.session.commit()
            flash('All users have been unsubscribed', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect admin password', 'danger')
    
    return render_template_string('''
        <h2>Bulk Unsubscribe All Users</h2>
        <form method="POST">
            {{ form.csrf_token }}
            <p>Warning: This will unsubscribe ALL users from newsletters</p>
            {{ form.admin_password.label }} {{ form.admin_password() }}<br>
            <button type="submit" class="danger">Confirm Bulk Unsubscribe</button>
        </form>
        <p><a href="{{ url_for('admin_dashboard') }}">Back to Dashboard</a></p>
    ''', form=form)

@app.route('/profile')
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template_string('''
        <h1>User Profile</h1>
        <p>Email: {{ user.email }}</p>
        <p>Subscription Status: {{ 'Subscribed' if user.is_subscribed else 'Unsubscribed' }}</p>
        <p><a href="{{ url_for('logout') }}">Logout</a></p>
        {% if user.is_subscribed %}
            <form action="{{ url_for('unsubscribe') }}" method="POST">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <button type="submit">Unsubscribe</button>
            </form>
        {% endif %}
    ''', user=user)

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user.is_subscribed = False
    db.session.commit()
    flash('You have been unsubscribed', 'success')
    return redirect(url_for('user_profile'))

if __name__ == '__main__':
    app.run(debug=True)