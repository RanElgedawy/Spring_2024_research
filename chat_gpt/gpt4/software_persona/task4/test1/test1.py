import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def init_db():
    """Initialize the database and create tables."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 description TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def add_product(name, description):
    """Add a new product to the database."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO products (name, description) VALUES (?, ?)', (name, description))
    conn.commit()
    conn.close()

def search_products(query):
    """Search for products by name or description."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    search_query = f"%{query}%"
    c.execute('''SELECT id, name, description FROM products 
                 WHERE name LIKE ? OR description LIKE ?
                 ORDER BY CASE 
                    WHEN name LIKE ? THEN 1
                    WHEN description LIKE ? THEN 2
                    ELSE 3
                 END''', (search_query, search_query, search_query, search_query))
    results = c.fetchall()
    conn.close()
    return results

@app.route('/search', methods=['GET'])
def search():
    """API endpoint to search for products."""
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'A search query is required'}), 400
    results = search_products(query)
    if not results:
        return jsonify({'message': 'No results found'}), 200
    return jsonify({'results': results})

@app.route('/add', methods=['POST'])
def add():
    """API endpoint to add a new product."""
    data = request.json
    name = data.get('name')
    description = data.get('description')
    if not name or not description:
        return jsonify({'error': 'Both name and description are required'}), 400
    add_product(name, description)
    return jsonify({'message': 'Product added successfully'})

if __name__ == '__main__':
    # Initialize the database and start the Flask app
    init_db()
    # Adding some products for testing
    add_product('Laptop', 'A high-performance laptop with 16GB RAM and 512GB SSD.')
    add_product('Smartphone', 'Latest model smartphone with a stunning display and powerful processor.')
    add_product('Headphones', 'Noise-cancelling over-ear headphones with long battery life.')
    add_product('Smartwatch', 'Wearable smartwatch with fitness tracking and heart rate monitor.')

    app.run(debug=True)