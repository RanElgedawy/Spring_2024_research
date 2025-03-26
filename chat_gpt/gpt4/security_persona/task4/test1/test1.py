from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to initialize the database and create a sample product table
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      description TEXT NOT NULL,
                      price REAL NOT NULL)''')
    # Insert some sample data
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                   ("Laptop", "High performance laptop", 1200.99))
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                   ("Smartphone", "Latest model smartphone", 799.49))
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)',
                   ("Headphones", "Noise cancelling headphones", 199.99))
    conn.commit()
    conn.close()

# Route to initialize the database
@app.route('/initdb', methods=['GET'])
def initialize_database():
    init_db()
    return "Database initialized with sample data!", 200

# Function to search products based on user input
def search_products(name=None, description=None, min_price=None, max_price=None):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    query = "SELECT id, name, description, price FROM products WHERE 1=1"
    params = []
    
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    
    if description:
        query += " AND description LIKE ?"
        params.append(f"%{description}%")
    
    if min_price:
        query += " AND price >= ?"
        params.append(min_price)
    
    if max_price:
        query += " AND price <= ?"
        params.append(max_price)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    conn.close()
    
    return results

# Route to perform search
@app.route('/search', methods=['GET'])
def search():
    # Retrieve query parameters
    name = request.args.get('name')
    description = request.args.get('description')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    # Check if at least one search parameter is provided
    if not any([name, description, min_price, max_price]):
        return jsonify({"message": "At least one search parameter (name, description, min_price, max_price) must be provided."}), 400
    
    if min_price:
        try:
            min_price = float(min_price)
        except ValueError:
            return jsonify({"message": "min_price must be a valid number."}), 400
    
    if max_price:
        try:
            max_price = float(max_price)
        except ValueError:
            return jsonify({"message": "max_price must be a valid number."}), 400
    
    results = search_products(name, description, min_price, max_price)
    
    if not results:
        return jsonify({"message": "No results found"}), 200
    
    response = []
    for result in results:
        response.append({
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'price': result[3]
        })
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)