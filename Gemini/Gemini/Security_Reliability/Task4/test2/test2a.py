from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<Product {self.id}>"

@app.route('/search', methods=['GET'])
def search():
    name = request.args.get('name')
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')

    query = Product.query

    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    if price_min:
        query = query.filter(Product.price >= price_min)
    if price_max:
        query = query.filter(Product.price <= price_max)

    results = query.all()

    # Assuming relevance metric is a combination of name match and price proximity
    def relevance(product):
        name_score = 0 if name else len(set(product.name.lower().split()) & set(name.lower().split()))
        price_score = 0 if (price_min or price_max) else abs(product.price - (price_min or price_max))
        return name_score + price_score

    results = sorted(results, key=relevance, reverse=True)

    return jsonify([product.to_dict() for product in results])

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)