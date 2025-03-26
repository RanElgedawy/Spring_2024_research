from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Create database and table if they don't exist
def create_database():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL)''')
    conn.commit()
    conn.close()

# Function to add a product to the database
def add_product(name, description, price):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    conn.commit()
    conn.close()

# Function to search products based on various criteria
def search_products(query):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()

    # Use parameterized queries to prevent SQL injection
    c.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ? OR price >= ?", ('%'+query+'%', '%'+query+'%', query))
    results = c.fetchall()
    conn.close()

    # You can implement a more sophisticated ranking algorithm here
    # For simplicity, we'll return results based on relevance
    return results

# Flask route for searching products
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'})
    results = search_products(query)
    if not results:
        return jsonify({'error': 'No results found'})
    return jsonify(results)

if __name__ == '__main__':
    create_database()

    add_product("Product A", "A great product", 19.99)
    add_product("Product B", "Another good product", 24.99)
    add_product("Product C", "A product with a long description", 15.99)

    app.run(debug=True)