from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)

# Search function using SQLAlchemy text queries
@app.route('/search', methods=['GET'])
def search_products():
    search_term = request.args.get('q', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    # Base query to search for the product
    query = "SELECT * FROM Product WHERE (name LIKE :search OR description LIKE :search)"
    params = {'search': f'%{search_term}%'}

    # Add price filters if provided
    if min_price is not None:
        query += " AND price >= :min_price"
        params['min_price'] = min_price
    if max_price is not None:
        query += " AND price <= :max_price"
        params['max_price'] = max_price

    # Execute the query safely
    products = db.session.execute(text(query), params).fetchall()

    # Return the results as JSON
    result = [{'id': p.id, 'name': p.name, 'price': p.price, 'description': p.description} for p in products]
    return jsonify(result)

# Add some sample data
@app.before_first_request
def create_tables():
    db.drop_all()
    db.create_all()

    # Add sample products (only if the table is empty)
    if not Product.query.first():
        sample_products = [
            Product(name='Laptop', price=999.99, description='A high performance laptop'),
            Product(name='Smartphone', price=499.99, description='Latest model smartphone with powerful features'),
            Product(name='Tablet', price=299.99, description='Lightweight tablet for everyday use'),
            Product(name='Headphones', price=199.99, description='Noise-cancelling over-ear headphones'),
            Product(name='Smartwatch', price=249.99, description='Fitness tracking smartwatch with GPS'),
        ]
        db.session.bulk_save_objects(sample_products)
        db.session.commit()

# Test endpoint to retrieve all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    result = [{'id': p.id, 'name': p.name, 'price': p.price, 'description': p.description} for p in products]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)