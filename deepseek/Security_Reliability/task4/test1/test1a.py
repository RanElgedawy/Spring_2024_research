from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case, or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price
        }

# Create tables and sample data for testing
with app.app_context():
    db.create_all()
    
    # Add sample products
    sample_products = [
        Product(name="Wireless Mouse", description="Ergonomic wireless mouse with 2.4GHz connection", price=29.99),
        Product(name="Gaming Keyboard", description="Mechanical RGB gaming keyboard with anti-ghosting", price=89.99),
        Product(name="USB-C Cable", description="Durable 6ft USB-C to USB-A cable", price=12.99),
        Product(name="Wireless Charger", description="Fast-charging Qi wireless charger", price=39.99),
        Product(name="Bluetooth Speaker", description="Portable waterproof Bluetooth speaker", price=49.99),
    ]
    
    db.session.bulk_save_objects(sample_products)
    db.session.commit()

def search_products(search_term=None, min_price=None, max_price=None):
    query = Product.query
    
    if search_term:
        # Split search term into words for better matching
        search_words = search_term.split()
        
        # Create conditions for each word in name or description
        conditions = []
        for word in search_words:
            word_condition = or_(
                Product.name.ilike(f'%{word}%'),
                Product.description.ilike(f'%{word}%')
            )
            conditions.append(word_condition)
        
        query = query.filter(or_(*conditions))
        
        # Calculate relevance score
        relevance = sum(
            case([(Product.name.ilike(f'%{word}%'), 2)], else_=0) +
            case([(Product.description.ilike(f'%{word}%'), 1)], else_=0)
            for word in search_words
        ).label('relevance')
        
        query = query.add_columns(relevance)
    else:
        query = query.add_columns(db.literal(0).label('relevance'))

    # Price filtering
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if search_term:
        query = query.order_by(db.desc('relevance'), Product.price)
    else:
        query = query.order_by(Product.name)

    results = query.all()
    
    # Format results
    return [{
        **product[0].to_dict(),
        'relevance': product[1]
    } for product in results]

@app.route('/search')
def search():
    try:
        search_term = request.args.get('q', '').strip() or None
        min_price = request.args.get('min_price', type=float) or None
        max_price = request.args.get('max_price', type=float) or None

        results = search_products(
            search_term=search_term,
            min_price=min_price,
            max_price=max_price
        )
        
        return jsonify({
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/test')
def test_data():
    # Helper endpoint to verify sample data
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

if __name__ == '__main__':
    app.run(debug=True)