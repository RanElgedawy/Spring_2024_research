from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, case, desc

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

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category
        }

@app.route('/search', methods=['GET'])
def search_products():
    search_term = request.args.get('query', '')
    
    if not search_term:
        return jsonify([])
    
    # Create search conditions for name and description
    name_match = Product.name.ilike(f'%{search_term}%')
    desc_match = Product.description.ilike(f'%{search_term}%')
    
    # Calculate relevance score (higher weight for name matches)
    relevance = case(
        [
            (name_match, 2),
            (desc_match, 1)
        ],
        else_=0
    ).label('relevance')
    
    results = db.session.query(
        Product,
        relevance
    ).filter(
        or_(name_match, desc_match)
    ).order_by(
        desc(relevance),
        Product.name
    ).all()
    
    # Format results with relevance score
    formatted_results = []
    for product, score in results:
        product_data = product.to_dict()
        product_data['relevance'] = score
        formatted_results.append(product_data)
    
    return jsonify(formatted_results)

@app.route('/test', methods=['GET'])
def test_search():
    try:
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Add test products
        test_products = [
            Product(
                name='Cotton T-Shirt',
                description='Comfortable cotton t-shirt for everyday wear',
                price=19.99,
                category='Clothing'
            ),
            Product(
                name='Leather Notebook',
                description='Premium leather-bound writing journal',
                price=29.95,
                category='Stationery'
            ),
            Product(
                name='Running Shoes',
                description='High-performance athletic shoes with cushioning',
                price=89.99,
                category='Footwear'
            ),
            Product(
                name='Cotton Blend Socks',
                description='Soft cotton socks 3-pack',
                price=12.50,
                category='Clothing'
            )
        ]
        
        db.session.bulk_save_objects(test_products)
        db.session.commit()
        
        # Perform sample search
        sample_search = Product.query.filter(
            or_(
                Product.name.ilike('%cotton%'),
                Product.description.ilike('%cotton%')
            )
        ).all()
        
        return jsonify({
            'message': 'Test data added successfully',
            'sample_results': [p.to_dict() for p in sample_search]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)