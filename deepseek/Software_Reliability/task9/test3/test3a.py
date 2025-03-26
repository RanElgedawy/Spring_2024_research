from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True, nullable=False)

class UnsubscribeReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Verify user identity
        if user:
            # Update subscription status
            user.is_subscribed = False
            reason_text = request.form.get('reason', '').strip()
            
            if reason_text:
                unsubscribe_reason = UnsubscribeReason(
                    user_id=user.id,
                    reason=reason_text
                )
                db.session.add(unsubscribe_reason)
            
            db.session.commit()
            return render_template('unsubscribe_success.html')
        
        return "User not found", 404
    
    return render_template('unsubscribe_form.html')

# Test routes
@app.route('/test/create_test_user/<email>')
def create_test_user(email):
    try:
        user = User(email=email, is_subscribed=True)
        db.session.add(user)
        db.session.commit()
        return f"Test user {email} created successfully"
    except Exception as e:
        return str(e), 400

@app.route('/test/login/<email>')
def test_login(email):
    user = User.query.filter_by(email=email).first()
    if user:
        session['user_id'] = user.id
        return f"Logged in as {email}"
    return "User not found", 404

@app.route('/test/logout')
def test_logout():
    session.pop('user_id', None)
    return "Logged out"

@app.route('/test/check_subscription/<email>')
def check_subscription(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return f"Subscription status for {email}: {user.is_subscribed}"
    return "User not found", 404

if __name__ == '__main__':
    app.run(debug=True)