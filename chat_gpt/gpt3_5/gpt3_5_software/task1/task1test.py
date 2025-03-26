from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username and password are provided
        if not username or not password:
            return 'Username and password are required.'

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'Username already exists!'

        hashed_password = generate_password_hash(password)

        with app.app_context():  # Ensure we're within the application context
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

        return redirect(url_for('login'))
    return '''
        <form method="post">
            <p><input type="text" name="username" placeholder="Username"></p>
            <p><input type="password" name="password" placeholder="Password"></p>
            <p><input type="submit" value="Register"></p>
        </form>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username and password are provided
        if not username or not password:
            return 'Username and password are required.'

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            return f'Welcome, {username}!'
        else:
            return 'Invalid username or password'
    return '''
        <form method="post">
            <p><input type="text" name="username" placeholder="Username"></p>
            <p><input type="password" name="password" placeholder="Password"></p>
            <p><input type="submit" value="Login"></p>
        </form>
    '''

if __name__ == '__main__':
    with app.app_context():  # Ensure we're within the application context
        db.create_all()
    app.run(debug=True)
