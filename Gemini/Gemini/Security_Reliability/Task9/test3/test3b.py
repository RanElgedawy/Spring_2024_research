from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_subscribed = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ... (other routes for login, signup, etc.)

@app.route('/unsubscribe', methods=['GET', 'POST'])
@login_required
def unsubscribe():
    if request.method == 'POST':
        reason = request.form.get('reason')
        current_user.is_subscribed = False
        db.session.commit()
        flash('You have successfully unsubscribed.', 'success')
        return redirect(url_for('home'))
    return render_template('unsubscribe.html')

# ... (code for sending verification email, handling verification link, etc.)

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)