from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/my_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define your Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)

    def __repr__(self):
        return f'<Product {self.name}>'

# Define the search endpoint
@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')

    # Check if query parameter is present
    if not query:
        return jsonify({'message': 'No query parameter provided'})

    # Calculate relevance score based on name similarity and price
    score = func.levenshtein(func.lower(Product.name), func.lower(query)) + (Product.price - float(query))

    # Perform the search and rank results based on relevance score
    results = db.session.query(Product, score.label('score')).filter(
        (Product.name.ilike(f'%{query}%')) |
        (Product.description.ilike(f'%{query}%'))
    ).order_by('score').all()

    # If no results found, return a message
    if not results:
        return jsonify({'message': 'No results found'})

    # Convert results to a list of dictionaries
    results_dict = [{'id': result.Product.id, 'name': result.Product.name, 'description': result.Product.description, 'price': result.Product.price, 'score': result.score} for result in results]

    return jsonify(results_dict)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)