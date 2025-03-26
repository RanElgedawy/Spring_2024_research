from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)

@app.route('/init_db')
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
    return jsonify({'message': 'Database initialized'})

@app.route('/add_sample')
def add_sample():
    products = [
        Product(name='Wireless Mouse', description='Ergonomic wireless mouse with 2.4GHz connection', price=29.99),
        Product(name='Mechanical Keyboard', description='RGB backlit mechanical keyboard with blue switches', price=89.99),
        Product(name='Gaming Monitor', description='27" 144Hz IPS gaming monitor with HDR', price=349.99),
        Product(name='Noise-Canceling Headphones', description='Bluetooth headphones with active noise cancellation', price=199.99),
    ]
    db.session.bulk_save_objects(products)
    db.session.commit()
    return jsonify({'message': 'Sample products added', 'count': len(products)})

@app.route('/search')
def product_search():
    # Check if any search parameters are provided
    if not any(param in request.args for param in ['name', 'description', 'price']):
        return jsonify({
            'error': 'At least one search parameter is required',
            'message': 'Please provide name, description, or price parameters'
        }), 400

    # Get and validate parameters
    name = request.args.get('name', type=str)
    description = request.args.get('description', type=str)
    price = request.args.get('price', type=float)
    
    query = Product.query
    
    # Build secure filters
    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    if description:
        query = query.filter(Product.description.ilike(f'%{description}%'))
    if price is not None:
        query = query.filter(Product.price == price)
    
    # Order by relevance (name matches first, then description)
    results = query.order_by(
        Product.name.asc(),
        Product.description.asc()
    ).all()
    
    if not results:
        return jsonify({
            'message': 'No results found',
            'results': []
        })
    
    return jsonify({
        'results': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price
        } for p in results]
    })

@app.route('/test')
def test_interface():
    return render_template_string('''
        <h2>Test Product Search</h2>
        <form action="/search" method="GET">
            <input type="text" name="name" placeholder="Product name"><br>
            <input type="text" name="description" placeholder="Description contains"><br>
            <input type="number" step="0.01" name="price" placeholder="Exact price"><br>
            <input type="submit" value="Search">
        </form>
        <p><a href="/add_sample">Add Sample Data</a></p>
    ''')

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)