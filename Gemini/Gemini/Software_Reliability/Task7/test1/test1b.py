from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import request, make_response, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # Create a secure cookie with a time limit
            s = TimedJSONWebSignatureSerializer('your_secret_key', expires_in=3600)  # 1 hour
            token = s.dumps({'user_id': user.id})
            response = make_response(redirect(url_for('home')))
            response.set_cookie('session_token', token, samesite='Lax')
            return response
    return render_template('login.html')

def home():
    session_token = request.cookies.get('session_token')
    if session_token:
        try:
            s = TimedJSONWebSignatureSerializer('your_secret_key')
            data = s.loads(session_token)
            user_id = data['user_id']
            user = User.query.get(user_id)
            if user:
                return render_template('home.html', user=user)
        except Exception as e:
            pass
    return redirect(url_for('login'))