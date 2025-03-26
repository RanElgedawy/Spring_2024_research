import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Connect to the SQLite database
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Manually added code to prevent conflict with existing tables
cursor.execute("DROP TABLE IF EXISTS products")

# Create a table to store products
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT
    )
''')

# Sample data
products = [
    ('1', 'Product 1', 'This is the description for Product 1'),
    ('2', 'Product 2', 'Description for Product 2'),
    ('3', 'Product 3', 'Description for Product 3'),
    # Add more sample products as needed
]

# Insert sample data into the products table
cursor.executemany('INSERT INTO products (id, name, description) VALUES (?, ?, ?)', products)

# Commit changes
conn.commit()

@app.route('/search', methods=['GET'])
def search_products():
    # Check if 'query' parameter is present in the API call
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    # Connect to the SQLite database
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Search for products by name or description
    cursor.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", ('%' + query + '%', '%' + query + '%'))
    results = cursor.fetchall()

    conn.close()
    
    if results:
        return jsonify({'results': results}), 200
    else:
        return jsonify({'message': 'No results found'}), 404

if __name__ == '__main__':
    app.run(debug=True)