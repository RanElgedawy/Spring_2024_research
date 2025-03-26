import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Connect to SQLite Database
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT
    )
    ''')

    # Insert sample data (only if table is empty)
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        products = [
            ("Laptop", 999.99, "A high-performance laptop for professionals."),
            ("Smartphone", 699.99, "A smartphone with an excellent camera and display."),
            ("Headphones", 199.99, "Noise-cancelling wireless headphones."),
            ("Monitor", 249.99, "A 24-inch 1080p monitor for work and gaming."),
        ]
        cursor.executemany('INSERT INTO products (name, price, description) VALUES (?, ?, ?)', products)

    conn.commit()
    conn.close()

# Function to search the database
def search_products(search_term, filter_by='name'):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # SQL query with parameterized input to prevent SQL injection
    query = f"SELECT * FROM products WHERE {filter_by} LIKE ?"
    cursor.execute(query, (f'%{search_term}%',))
    results = cursor.fetchall()
    conn.close()

    # Format the results
    return [
        {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'description': row[3]
        } for row in results
    ]

# API Endpoint for searching products
@app.route('/search', methods=['GET'])
def search():
    search_term = request.args.get('term', '')
    filter_by = request.args.get('filter_by', 'name')  # can be 'name', 'price', or 'description'

    # Validate filter_by parameter to ensure it's a valid column name
    if filter_by not in ['name', 'price', 'description']:
        return jsonify({'error': 'Invalid filter_by parameter'}), 400

    # Perform search
    results = search_products(search_term, filter_by)

    return jsonify(results)

if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Run the Flask app
    app.run(debug=True)