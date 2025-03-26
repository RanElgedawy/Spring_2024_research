import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify

# Create a Flask app instance (you'll likely have one already)
app = Flask(__name__)

# Configure SQLAlchemy with SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

# Create a Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Product {self.id}>"

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')

    # Implement search logic based on your chosen relevance metric
    # Here's a simple example using full-text search:
    results = Product.query.filter(Product.name.ilike(f'%{query}%') | Product.description.ilike(f'%{query}%')).all()

    return jsonify([product.to_dict() for product in results])

def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'description': self.description
    }

product1 = Product(name="Laptop", description="Powerful laptop for work and play")
product2 = Product(name="Phone", description="Stylish smartphone with great camera")
db.session.add(product1)
db.session.add(product2)
db.session.commit()