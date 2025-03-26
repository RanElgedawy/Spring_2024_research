from flask import Flask, request, redirect, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta

# HTML Templates
login_template = """
<!DOCTYPE html>
<html>
<body>
    <h1>Login</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

dashboard_template = """
<!DOCTYPE html>
<html>
<body>
    <h1>Welcome to Dashboard</h1>
    <a href="/logout">Logout</a>
</body>
</html>
"""

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True  # Should be True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.jinja_env.globals.update(login_template=login_template, dashboard_template=dashboard_template)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

def create_test_user():
    with app.app_context():
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            hashed_pw = generate_password_hash('testpass123')
            new_user = User(username='testuser', password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()

create_test_user()

@app.before_request
def check_auth():
    if request.endpoint in ['login', 'static']:
        return
    session_token = request.cookies.get('session_token')
    if not session_token:
        return redirect('/login')
    
    session = Session.query.filter_by(token=session_token).first()
    if not session or session.expires_at < datetime.now():
        if session:
            db.session.delete(session)
            db.session.commit()
        return redirect('/login')

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Create new session
            token = secrets.token_urlsafe(64)
            expires_at = datetime.now() + timedelta(days=1)
            
            new_session = Session(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            db.session.add(new_session)
            db.session.commit()
            
            response = make_response(redirect('/'))
            response.set_cookie(
                'session_token',
                value=token,
                expires=expires_at,
                secure=True,
                httponly=True,
                samesite='Lax'
                # Domain not set to restrict to current domain only
            )
            return response
        
        return 'Invalid credentials', 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        session = Session.query.filter_by(token=session_token).first()
        if session:
            db.session.delete(session)
            db.session.commit()
    
    response = make_response(redirect('/login'))
    response.set_cookie('session_token', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(ssl_context='adhoc', port=443)  # HTTPS required for Secure cookies