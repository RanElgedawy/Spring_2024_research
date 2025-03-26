# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, case, Float

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
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

@app.route('/search', methods=['GET'])
def search_products():
    search_term = request.args.get('q', '').strip()
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    # Input validation
    try:
        min_price = float(min_price) if min_price else None
        max_price = float(max_price) if max_price else None
    except ValueError:
        return jsonify({'error': 'Invalid price format'}), 400

    if min_price is not None and min_price < 0:
        return jsonify({'error': 'Price cannot be negative'}), 400
    if max_price is not None and max_price < 0:
        return jsonify({'error': 'Price cannot be negative'}), 400

    # Build query
    query = Product.query

    # Price range filter
    if min_price is not None or max_price is not None:
        price_filters = []
        if min_price is not None:
            price_filters.append(Product.price >= min_price)
        if max_price is not None:
            price_filters.append(Product.price <= max_price)
        query = query.filter(and_(*price_filters))

    # Text search filter
    if search_term:
        search_filter = or_(
            Product.name.ilike(f'%{search_term}%'),
            Product.description.ilike(f'%{search_term}%')
        )
        query = query.filter(search_filter)

        # Relevance scoring (case-insensitive matches in name get higher weight)
        relevance = case(
            [
                (Product.name.ilike(f'%{search_term}%'), 2.0),
                (Product.description.ilike(f'%{search_term}%'), 1.0)
            ],
            else_=0.0
        ).cast(Float)

        query = query.add_columns(relevance.label('relevance'))
        query = query.order_by(db.desc('relevance'))
    else:
        query = query.order_by(Product.name)

    # Execute query
    results = query.all()

    # Format results
    if search_term:
        products = [{'product': p[0].to_dict(), 'relevance': p[1]} for p in results]
    else:
        products = [{'product': p.to_dict(), 'relevance': None} for p in results]

    return jsonify({'results': products})

def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)