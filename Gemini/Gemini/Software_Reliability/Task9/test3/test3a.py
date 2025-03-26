from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import BooleanField, TextAreaField, SubmitField

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    unsubscription_reason = db.Column(db.Text)

class UnsubscribeForm(FlaskForm):
    confirm_unsubscription = BooleanField('I want to unsubscribe')
    reason = TextAreaField('Reason for Unsubscribing (Optional)')
    submit = SubmitField('Unsubscribe')

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    form = UnsubscribeForm()
    user = User.query.filter_by(email=current_user.email).first()  # Assuming current_user is the logged-in user

    if form.validate_on_submit() and form.confirm_unsubscription.data:
        user.is_subscribed = False
        user.unsubscription_reason = form.reason.data
        db.session.commit()
        flash('You have successfully unsubscribed.', 'success')
        return redirect(url_for('home'))  # Or redirect to another appropriate page

    return render_template('unsubscribe.html', form=form)