from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(100))

    def __repr__(self):
        return f'<Product {self.name}>'

with app.app_context():
    db.create_all()

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def calculate_relevance(query, product):
    query_terms = set(preprocess_text(query).split())
    name_terms = set(preprocess_text(product.name).split())
    desc_terms = set(preprocess_text(product.description).split())
    
    name_matches = len(query_terms & name_terms)
    desc_matches = len(query_terms & desc_terms)
    
    return (name_matches * 2) + desc_matches

def perform_search(search_query):
    if not search_query:
        return []
    
    search_query = preprocess_text(search_query)
    terms = search_query.split()

    conditions = []
    for term in terms:
        term_pattern = f'%{term}%'
        conditions.append(
            or_(
                Product.name.ilike(term_pattern),
                Product.description.ilike(term_pattern)
            )
        )

    results = Product.query.filter(*conditions).all()
    scored_results = [(product, calculate_relevance(search_query, product)) 
                     for product in results]
    return sorted(scored_results, key=lambda x: (-x[1], x[0].price))

@app.route('/search')
def search_products():
    search_query = request.args.get('q', '')
    results = perform_search(search_query)
    
    response = [{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category': product.category,
        'relevance_score': score
    } for product, score in results]
    
    if not response and search_query:
        return jsonify({'message': 'No results found', 'results': []})
    return jsonify(response)

@app.route('/add_test_data')
def add_test_data():
    test_products = [
        Product(name='Wireless Headphones', 
                description='Noise-cancelling Bluetooth headphones',
                price=199.99, category='Audio'),
        Product(name='Smartwatch', 
                description='Fitness tracker with heart rate monitor',
                price=159.99, category='Wearables'),
        Product(name='Laptop Bag', 
                description='Water-resistant 15" laptop backpack',
                price=49.99, category='Accessories')
    ]
    db.session.bulk_save_objects(test_products)
    db.session.commit()
    return 'Test data added!'

@app.route('/test_search')
def test_search_interface():
    search_query = request.args.get('q', '')
    results = []
    if search_query:
        search_results = perform_search(search_query)
        results = [{'product': p, 'score': s} for p, s in search_results]
    
    return render_template_string('''
        <h2>Product Search</h2>
        <form method="GET">
            <input type="text" name="q" value="{{ query }}" placeholder="Search products..." size="40">
            <button type="submit">Search</button>
        </form>
        
        {% if query %}
            <h3>Search results for "{{ query }}"</h3>
            {% if results %}
                <ul>
                {% for item in results %}
                    <li>
                        <strong>{{ item.product.name }}</strong><br>
                        {{ item.product.description }}<br>
                        Price: ${{ "%.2f"|format(item.product.price) }}<br>
                        Category: {{ item.product.category }}<br>
                        Relevance score: {{ item.score }}
                    </li>
                {% endfor %}
                </ul>
            {% else %}
                <p style="color: red;">No results found</p>
            {% endif %}
        {% endif %}
    ''', query=search_query, results=results)

if __name__ == '__main__':
    app.run(debug=True)