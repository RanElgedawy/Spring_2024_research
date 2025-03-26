from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Product model
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

def initialize_database():
    # Create regular tables
    db.drop_all()
    db.create_all()

    # Create FTS5 virtual table using raw SQL
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS product_search 
        USING fts5(product_id, name, description, tokenize="porter")
    ''')
    conn.commit()
    conn.close()

@app.route('/add_test_data', methods=['POST'])
def add_test_data():
    # Sample products
    test_products = [
        Product(
            name="Running Shoes",
            description="High-performance running shoes with cushioning technology",
            price=129.99,
            category="Footwear"
        ),
        Product(
            name="Wireless Headphones",
            description="Noise-cancelling Bluetooth headphones with premium sound",
            price=199.99,
            category="Electronics"
        ),
        Product(
            name="Yoga Mat",
            description="Eco-friendly extra thick yoga mat for all exercises",
            price=49.99,
            category="Fitness"
        ),
        Product(
            name="Coffee Maker",
            description="Programmable coffee machine with thermal carafe",
            price=89.99,
            category="Kitchen"
        )
    ]

    # Add to database
    db.session.add_all(test_products)
    db.session.commit()

    # Add to FTS table
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    for product in test_products:
        cursor.execute('''
            INSERT INTO product_search (product_id, name, description)
            VALUES (?, ?, ?)
        ''', (product.id, product.name, product.description))
    conn.commit()
    conn.close()

    return jsonify({"message": "Test data added successfully"}), 201

@app.route('/search', methods=['GET'])
def search_products():
    search_query = request.args.get('q', '')
    if not search_query:
        return jsonify({"error": "Missing search query"}), 400

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Search using FTS5 with ranking
    cursor.execute('''
        SELECT 
            p.id,
            p.name,
            p.description,
            p.price,
            p.category,
            bm25(product_search) AS relevance
        FROM product_search
        JOIN products p ON product_search.product_id = p.id
        WHERE product_search MATCH ?
        ORDER BY relevance
    ''', (f'"{search_query}"*',))  # Add prefix search with *

    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': row[3],
            'category': row[4],
            'relevance': row[5]
        })

    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)