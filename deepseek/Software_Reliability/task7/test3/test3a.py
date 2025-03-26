from flask import Flask, request, make_response, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secure-secret-key'  # Change for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

# Session Model
class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(32), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

# Create tables and test user
with app.app_context():
    db.drop_all()
    db.create_all()
    if not User.query.first():
        test_user = User(
            username='testuser',
            password_hash=generate_password_hash('testpass')
        )
        db.session.add(test_user)
        db.session.commit()

def login_required(f):
    def decorated(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            return redirect(url_for('login'))
        
        session = Session.query.filter_by(token=session_token).first()
        if not session or session.expires_at < datetime.utcnow():
            return redirect(url_for('logout'))
        
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return '''Welcome! <a href="/login">Login</a> | <a href="/dashboard">Dashboard</a>'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Generate session token
            token = secrets.token_hex(16)
            expires_at = datetime.utcnow() + timedelta(minutes=30)
            
            # Store session
            db.session.add(Session(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            ))
            db.session.commit()
            
            # Set cookie
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie(
                'session_token',
                token,
                httponly=True,
                secure=False,  # Set to True in production (requires HTTPS)
                samesite='Lax',
                max_age=1800  # 30 minutes
                # Domain parameter omitted to restrict to current domain
            )
            return response
        return 'Invalid credentials!'
    return render_template_string('''
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    ''')

@app.route('/dashboard')
@login_required
def dashboard():
    return '''Logged in! <a href="/logout">Logout</a>'''

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        Session.query.filter_by(token=token).delete()
        db.session.commit()
    
    response = make_response(redirect(url_for('home')))
    response.set_cookie('session_token', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(debug=True)