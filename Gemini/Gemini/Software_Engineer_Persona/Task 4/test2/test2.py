from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Create a database connection
conn = sqlite3.connect('products.db')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS products")
# Create a table to store product data
c.execute('''CREATE TABLE IF NOT EXISTS products
             (id INTEGER PRIMARY KEY,
              name TEXT,
              description TEXT)''')
conn.commit()

# Sample products for testing
products = [
    {'name': 'Laptop', 'description': 'Powerful laptop for work and play'},
    {'name': 'Smartphone', 'description': 'Latest smartphone with advanced features'},
    {'name': 'Headphones', 'description': 'High-quality noise-canceling headphones'}
]

# Populate the database with sample products
for product in products:
    c.execute("INSERT INTO products (name, description) VALUES (?, ?)", (product['name'], product['description']))
conn.commit()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'})

    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    # Search by product name and description
    c.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", ('%' + query + '%', '%' + query + '%'))
    results = c.fetchall()

    if not results:
        return jsonify({'message': 'No results found'})

    # Convert results to a JSON format
    response = []
    for row in results:
        response.append({'id': row[0], 'name': row[1], 'description': row[2]})

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)