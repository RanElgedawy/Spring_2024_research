import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Step 1: Set up the database and tables
def create_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Create the products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    ''')
    
    # Insert sample data
    cursor.execute("INSERT INTO products (name, description) VALUES ('Laptop', 'High-performance laptop with 16GB RAM and 512GB SSD')")
    cursor.execute("INSERT INTO products (name, description) VALUES ('Smartphone', 'Latest model smartphone with 5G connectivity')")
    cursor.execute("INSERT INTO products (name, description) VALUES ('Headphones', 'Wireless headphones with noise cancellation')")
    cursor.execute("INSERT INTO products (name, description) VALUES ('Monitor', '24-inch monitor with 1080p resolution')")
    cursor.execute("INSERT INTO products (name, description) VALUES ('Keyboard', 'Mechanical keyboard with RGB lighting')")
    
    conn.commit()
    conn.close()

# Step 2: Implement the search function
def search_products(search_term):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # SQL query to search for products by name or description
    query = '''
    SELECT id, name, description,
    (CASE
        WHEN name LIKE ? THEN 1
        WHEN description LIKE ? THEN 2
        ELSE 3
    END) AS relevance
    FROM products
    WHERE name LIKE ? OR description LIKE ?
    ORDER BY relevance ASC
    '''
    
    # Search term with wildcard for partial matches
    wildcard_term = f'%{search_term}%'
    
    cursor.execute(query, (wildcard_term, wildcard_term, wildcard_term, wildcard_term))
    results = cursor.fetchall()
    
    conn.close()
    return results

# Step 3: API endpoint to handle search requests
@app.route('/search', methods=['GET'])
def search_api():
    search_term = request.args.get('q')
    
    # Check if the search term is provided
    if not search_term:
        return jsonify({"error": "Missing required parameter 'q'"}), 400
    
    results = search_products(search_term)
    
    if results:
        return jsonify({
            "results": [
                {"id": result[0], "name": result[1], "description": result[2]}
                for result in results
            ]
        })
    else:
        return jsonify({"message": "No results found."})

# Step 4: Initialize the database and run the app
if __name__ == "__main__":
    create_database()  # Create the database and insert sample data
    app.run(debug=True)  # Run the Flask app