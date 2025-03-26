from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255))

    def __repr__(self):
        return f"<Product {self.id}>"

# ... (other routes and authentication logic)

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Handle form submission for adding, modifying, or removing products
        # ... (validation, database operations, etc.)
        return redirect(url_for('admin_products'))

    products = Product.query.all()
    return render_template('admin_products.html', products=products)

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)