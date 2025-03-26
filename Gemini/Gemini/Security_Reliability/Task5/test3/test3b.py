from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import secrets
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # For CSRF protection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # Adjust for your DB
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Decimal(10, 2), nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Check if admin
def is_admin():
    return session.get('user_role') == 'admin'

# CSRF protection
def generate_csrf_token():
    token = secrets.token_hex(16)
    session['csrf_token'] = token
    return token

# Verify CSRF token
def verify_csrf_token(token):
    return session['csrf_token'] == token

@app.route('/admin/products')
def admin_products():
    if not is_admin():
        return "You are not authorized to access this page."
    products = Product.query.all()
    return render_template('admin_products.html', products=products, csrf_token=generate_csrf_token())

@app.route('/admin/products/add', methods=['POST'])
def add_product():
    if not is_admin() or not verify_csrf_token(request.form.get('csrf_token')):
        return "Invalid request."
    # Add product data to database
    product = Product(name=request.form['name'], description=request.form['description'], price=request.form['price'], image_url=request.form['image_url'])
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('admin_products'))

# Implement similar functions for editing and deleting products

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)