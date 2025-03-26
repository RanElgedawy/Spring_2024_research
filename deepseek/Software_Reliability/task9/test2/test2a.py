from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    newsletter_subscription = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class UnsubscriptionReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Create tables and test user
with app.app_context():
    db.drop_all()
    db.create_all()
    if not User.query.filter_by(email='test@example.com').first():
        test_user = User(email='test@example.com', newsletter_subscription=True)
        test_user.set_password('password')
        db.session.add(test_user)
        db.session.commit()

# HTML Templates
UNSUBSCRIBE_FORM = '''
<!DOCTYPE html>
<html>
<head><title>Unsubscribe</title></head>
<body>
    {% if message %}<p>{{ message }}</p>{% endif %}
    <h1>Unsubscribe from Newsletter</h1>
    <form method="POST">
        <label>Reason (optional):</label><br>
        <textarea name="reason" rows="4" cols="50"></textarea><br>
        <button type="submit">Unsubscribe</button>
    </form>
</body>
</html>
'''

# Routes
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update subscription status
        user.newsletter_subscription = False
        # Save reason if provided
        reason_text = request.form.get('reason', '').strip()
        if reason_text:
            reason = UnsubscriptionReason(user_id=user.id, reason=reason_text)
            db.session.add(reason)
        db.session.commit()
        return render_template_string(UNSUBSCRIBE_FORM, message="You have been unsubscribed successfully")
    
    return render_template_string(UNSUBSCRIBE_FORM)

# Test Routes
@app.route('/test_login', methods=['GET', 'POST'])
def test_login():
    if request.method == 'POST':
        user = User.query.filter_by(email='test@example.com').first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('unsubscribe'))
        return 'Invalid credentials'
    return '''
    <form method="POST">
        <input type="password" name="password" placeholder="Enter test password 'password'">
        <button type="submit">Login</button>
    </form>
    '''

@app.route('/subscription_status')
def subscription_status():
    if 'user_id' not in session:
        return 'Not logged in'
    user = User.query.get(session['user_id'])
    return f'Subscription status: {user.newsletter_subscription}'

@app.route('/test_subscribe')
def test_subscribe():
    if 'user_id' not in session:
        return 'Not logged in'
    user = User.query.get(session['user_id'])
    user.newsletter_subscription = True
    db.session.commit()
    return 'Subscribed successfully'

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('test_login'))

if __name__ == '__main__':
    app.run(debug=True)