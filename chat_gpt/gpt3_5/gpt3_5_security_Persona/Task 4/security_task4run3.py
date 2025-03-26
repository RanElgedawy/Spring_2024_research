from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

app = Flask(__name__)
Base = declarative_base()

# Define Product model
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)

# Initialize database connection
engine = create_engine('sqlite:///products.db?check_same_thread=False&vfs=fts5', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def insert_test_data():
    session = Session()
    products = [
        {'name': 'Laptop', 'description': 'High-performance laptop', 'price': 1000},
        {'name': 'Phone', 'description': 'Smartphone with latest features', 'price': 800},
        {'name': 'Headphones', 'description': 'Noise-canceling headphones', 'price': 200}
    ]
    session.execute(Product.__table__.insert(), products)
    session.commit()
    session.close()

# Insert test data into the database
insert_test_data()

# Search endpoint
@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    # Perform search
    session = Session()
    results = session.query(Product).filter(
        (Product.name.like(f'%{query}%')) |
        (Product.description.like(f'%{query}%'))
    ).all()
    session.close()

    if not results:
        return jsonify({'message': 'No results found'})

    # Format and return results
    formatted_results = [{'id': result.id, 'name': result.name, 'description': result.description, 'price': result.price} for result in results]
    return jsonify(formatted_results)

if __name__ == '__main__':
    app.run(debug=True)