from flask import Flask, request, redirect, url_for, make_response, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(36), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

# Create tables and test user
with app.app_context():
    db.drop_all()
    db.create_all()
    if not User.query.filter_by(username='test').first():
        test_user = User(username='test')
        test_user.set_password('test')
        db.session.add(test_user)
        db.session.commit()

# Helper function to validate sessions
def validate_session():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    
    session = Session.query.filter_by(session_token=session_token).first()
    if not session or session.expires_at < datetime.utcnow():
        return None
    
    return User.query.get(session.user_id)

# Routes
@app.route('/')
def home():
    user = validate_session()
    if not user:
        return redirect(url_for('login'))
    return f'Hello, {user.username}! <a href="/logout">Logout</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Create new session
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            new_session = Session(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at
            )
            
            db.session.add(new_session)
            db.session.commit()

            response = make_response(redirect(url_for('home')))
            response.set_cookie(
                'session_token',
                value=session_token,
                httponly=True,
                secure=False,  # Set to True in production
                samesite='Lax',
                max_age=3600  # 1 hour expiration
            )
            return response
        
        return 'Invalid credentials'
    
    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username" required><br>
            Password: <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        session = Session.query.filter_by(session_token=session_token).first()
        if session:
            db.session.delete(session)
            db.session.commit()
    
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session_token', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(debug=True)