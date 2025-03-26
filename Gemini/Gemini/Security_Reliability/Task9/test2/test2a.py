from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import smtplib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Replace with your DB URI
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_subscribed = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.email}>'

class UnsubscribeReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(255))

    def __repr__(self):
        return f'<UnsubscribeReason {self.reason}>'

# ... (rest of the application)