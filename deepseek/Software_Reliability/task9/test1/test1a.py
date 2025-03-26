from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from wtforms import Form, StringField, TextAreaField, validators

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    email = db.Column(db.String(120), primary_key=True)
    subscribed = db.Column(db.Boolean, default=True)
    unsubscribe_reason = db.Column(db.Text)
    unsubscribed_at = db.Column(db.DateTime)

class UnsubscribeForm(Form):
    reason = TextAreaField('Reason (optional)', [validators.Length(max=500)])

# Create tables and add test user
with app.app_context():
    db.drop_all()
    db.create_all()
    # Add test user if not exists
    if not User.query.get('test@example.com'):
        test_user = User(email='test@example.com', subscribed=True)
        db.session.add(test_user)
        db.session.commit()

@app.route('/')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['email'])
    return render_template('dashboard.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.get(email)
        if user:
            session['email'] = email
            return redirect(url_for('dashboard'))
        return 'User not found', 404
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['email'])
    form = UnsubscribeForm(request.form)
    
    if request.method == 'POST' and form.validate():
        user.subscribed = False
        user.unsubscribe_reason = form.reason.data
        user.unsubscribed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('unsubscribe.html', form=form, user=user)

if __name__ == '__main__':
    app.run(debug=True)