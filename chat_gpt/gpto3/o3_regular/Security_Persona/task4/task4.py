from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def create_connection():
    """Create an in-memory SQLite database connection with threading support."""
    return sqlite3.connect(":memory:", check_same_thread=False)

def create_table(conn):
    """Create a products table in the database."""
    create_table_sql = """
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    );
    """
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute(create_table_sql)
    conn.commit()

def insert_sample_data(conn):
    """Insert some sample product records."""
    products = [
        ("Laptop", "High-performance laptop for gaming and work", 999.99),
        ("Smartphone", "Latest model smartphone with advanced features", 799.99),
        ("Wireless Mouse", "Ergonomic wireless mouse", 29.99),
        ("Keyboard", "Mechanical keyboard with backlight", 59.99),
        ("Monitor", "24-inch Full HD monitor", 199.99),
    ]
    conn.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?);", products)
    conn.commit()

def search_products(conn, search_term=None, min_price=None, max_price=None):
    """
    Search for products using a search term and/or price filters.
    
    When a search_term is provided, a simple score is calculated:
      - +2 if the product name matches
      - +1 if the product description matches
    Results are then ordered by this score (descending) and price (ascending).
    
    All SQL parameters are safely passed to avoid SQL injection.
    """
    cursor = conn.cursor()
    
    # Start building the base query and parameters list
    query = "SELECT id, name, description, price"
    params = []
    
    # If a search term is given, compute a simple ranking score.
    if search_term:
        query += """,
        ((CASE WHEN name LIKE ? THEN 2 ELSE 0 END) +
         (CASE WHEN description LIKE ? THEN 1 ELSE 0 END)) AS score
        """
        pattern = f"%{search_term}%"
        params.extend([pattern, pattern])
        
    query += " FROM products WHERE 1=1"
    
    # Add filter for search term if provided (searching in name or description)
    if search_term:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([pattern, pattern])
    
    # Add optional price filters
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    # Order the results. If a search term is provided, sort by score.
    if search_term:
        query += " ORDER BY score DESC, price ASC"
    else:
        query += " ORDER BY id ASC"
    
    cursor.execute(query, params)
    return cursor.fetchall()

# Initialize the in-memory database and insert sample data
conn = create_connection()
create_table(conn)
insert_sample_data(conn)

@app.route('/search', methods=['GET'])
def search_api():
    """
    API endpoint to search for products.
    
    Expects at least one query parameter among:
    - search_term (string)
    - min_price (float)
    - max_price (float)
    
    If no parameters are provided, it returns a "No arguments provided" message.
    If no matching products are found, it returns "No results found".
    """
    # Retrieve query parameters from the API call
    search_term = request.args.get('search_term', default=None, type=str)
    min_price = request.args.get('min_price', default=None, type=float)
    max_price = request.args.get('max_price', default=None, type=float)
    
    # Check if any arguments are present
    if search_term is None and min_price is None and max_price is None:
        return jsonify({"message": "No arguments provided"}), 400
    
    results = search_products(conn, search_term, min_price, max_price)
    
    if not results:
        return jsonify({"message": "No results found"}), 200
    
    # Prepare the results in a JSON-friendly format
    products = []
    for row in results:
        product = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3]
        }
        products.append(product)
    
    return jsonify({"results": products}), 200

if __name__ == '__main__':
    app.run(debug=True)
