import re
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def init_db():
    """
    Initialize the database by creating the products table.
    If the table is empty, insert some sample products.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create the products table if it does not exist
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL
        )
    ''')
    # Check if there are any products already
    c.execute('SELECT COUNT(*) FROM products')
    count = c.fetchone()[0]
    if count == 0:
        # Insert sample products for testing
        sample_products = [
            ('Apple iPhone 13', 'Latest model with A15 chip and improved battery life', 999.99),
            ('Samsung Galaxy S21', 'High-end smartphone with excellent camera quality', 799.99),
            ('Google Pixel 6', 'Pure Android experience with exceptional camera performance', 699.99),
            ('Dell XPS 13 Laptop', 'Compact and powerful laptop for professionals', 1199.99),
            ('Sony WH-1000XM4 Headphones', 'Industry leading noise cancellation headphones', 349.99)
        ]
        c.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', sample_products)
    conn.commit()
    conn.close()

def compute_relevance(product, query):
    """
    Compute a relevance score for a product based on the number of times
    the query appears in the product name and description.
    - Each occurrence in the name is worth 10 points.
    - Each occurrence in the description is worth 1 point.
    
    Parameters:
      product: a tuple (id, name, description, price)
      query: the search term (string)
    
    Returns:
      An integer relevance score.
    """
    # Unpack product details
    _, name, description, _ = product
    description = description or ''
    query_lower = query.lower()
    
    # Count case-insensitive occurrences using regex
    name_occurrences = len(re.findall(re.escape(query_lower), name.lower()))
    description_occurrences = len(re.findall(re.escape(query_lower), description.lower()))
    
    score = 10 * name_occurrences + description_occurrences
    return score

def search_products(query):
    """
    Search for products whose name or description contains the query string.
    Only products with at least one occurrence of the query are returned,
    sorted by a computed relevance score in descending order.
    
    Parameters:
      query: the search term (string)
      
    Returns:
      A list of dictionaries representing matching products with their relevance scores.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Use SQL LIKE for a basic text match (case-insensitive for many SQLite builds)
    like_query = f'%{query}%'
    c.execute('SELECT * FROM products WHERE name LIKE ? OR description LIKE ?', (like_query, like_query))
    products = c.fetchall()
    conn.close()
    
    # Calculate the relevance score for each product and filter out zero scores
    scored_products = []
    for product in products:
        score = compute_relevance(product, query)
        if score > 0:
            scored_products.append((score, product))
    
    # Sort the results by relevance score (highest first)
    scored_products.sort(key=lambda x: x[0], reverse=True)
    
    # Build the output list
    results = []
    for score, product in scored_products:
        product_dict = {
            'id': product[0],
            'name': product[1],
            'description': product[2],
            'price': product[3],
            'relevance': score
        }
        results.append(product_dict)
    
    return results

@app.route('/search')
def search():
    """
    HTTP endpoint to search for products.
    Example usage: /search?q=iphone
    Returns a JSON list of matching products or a message if no results are found.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter "q" is required.'}), 400
    results = search_products(query)
    if not results:
        return jsonify({'message': 'No results found.'})
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    # Run the Flask app (access via http://localhost:5000)
    app.run(debug=True)
