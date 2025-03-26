from flask import Flask, request, redirect, make_response, render_template_string
from datetime import datetime, timedelta
import uuid
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
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
    token = db.Column(db.String(36), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

# Create tables and test user
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create test user if not exists
    if not User.query.filter_by(username='testuser').first():
        test_user = User(username='testuser')
        test_user.set_password('Testpass123!')
        db.session.add(test_user)
        db.session.commit()

# Middleware to check session
@app.before_request
def check_session():
    # Allow login and static routes
    if request.path in ['/login', '/static/style.css']:
        return
    
    session_token = request.cookies.get('session_token')
    
    if not session_token:
        return redirect('/login')
    
    valid_session = Session.query.filter_by(token=session_token).filter(
        Session.expires_at > datetime.utcnow()
    ).first()
    
    if not valid_session:
        return redirect('/login')

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Create session
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            new_session = Session(
                user_id=user.id,
                token=session_token,
                expires_at=expires_at
            )
            db.session.add(new_session)
            db.session.commit()
            
            response = make_response(redirect('/dashboard'))
            response.set_cookie(
                'session_token',
                value=session_token,
                expires=expires_at,
                httponly=True,
                secure=True,  # Set to False for local testing without HTTPS
                samesite='Strict',
                # Domain NOT set to restrict to current domain only
            )
            return response
        
        return 'Invalid credentials', 401
    
    return render_template_string('''
        <form method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <style>{% include 'static/style.css' %}</style>
    ''')

@app.route('/dashboard')
def dashboard():
    return render_template_string('''
        <h1>Dashboard</h1>
        <p>Logged in as {{ user.username }}</p>
        <a href="/logout">Logout</a>
        <style>{% include 'static/style.css' %}</style>
    ''', user=User.query.get(Session.query.filter_by(
        token=request.cookies.get('session_token')).first().user_id))

@app.route('/logout')
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        Session.query.filter_by(token=session_token).delete()
        db.session.commit()
    
    response = make_response(redirect('/login'))
    response.set_cookie('session_token', '', expires=0)
    return response

# Test CSS
@app.route('/static/style.css')
def css():
    return '''
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; }
        form { display: flex; flex-direction: column; gap: 10px; max-width: 300px; }
        input, button { padding: 8px; }
        a { color: #007bff; text-decoration: none; }
    '''

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)