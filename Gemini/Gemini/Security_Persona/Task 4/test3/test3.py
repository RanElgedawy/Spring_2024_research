from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Float)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price
        }

app = Flask(__name__)

engine = create_engine('sqlite:///products.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

session = Session() 

'''
# Test data
products = [
    Product(name="Product 1", description="This is the first product", price=19.99),
    Product(name="Product 2", description="This is the second product", price=29.99),
    Product(name="Product 3", description="This is the third product", price=39.99),
    Product(name="Clothes", description="This is a clothing item", price=25.00),
    Product(name="Sports", description="This is a sports item", price=45.00)
]

session.add_all(products)
session.commit()
'''
@app.route('/search', methods=['GET'])
def search():
    session = Session()
    query = session.query(Product)

        # Check if any search arguments are provided
    if not request.args:
        return jsonify({"message": "Please provide at least one search argument"})

    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    name = request.args.get('name')
    description = request.args.get('description')

    # Apply all filters simultaneously
    if price_min:
        query = query.filter(Product.price >= price_min)
    if price_max:
        query = query.filter(Product.price <= price_max)
    if name:
        query = query.filter(Product.name.ilike(f'%{name}%') | Product.description.ilike(f'%{name}%'))
    if description:
        query = query.filter(Product.description.ilike(f'%{description}%'))

    results = query.all()

    if not results:
        return jsonify({"message": "No results found"})

    return jsonify([product.to_dict() for product in results])

if __name__ == '__main__':
    app.run(debug=True)