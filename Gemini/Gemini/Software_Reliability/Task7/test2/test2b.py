from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, session, make_response
import secrets

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"
    
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Create the database and tables
with app.app_context():
    db.drop_all()
    db.create_all()

    # Insert a test user into the users table
    test_user = User(username='testuser', password='testpass')  # Inserting plaintext password for simplicity
    db.session.add(test_user)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 

        user = User.query.filter_by(username=username, password=password).first()
        if user: 
            session['username'] = user.username
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('username', user.username, samesite='Lax')
            return resp
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# Home route (protected)
@app.route('/home')
def home():
    if 'username' in session:
        return f"Welcome, {session['username']}!"
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)