from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def init_db():
    """Initialize the database and create the products table."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Enable FTS5 for full-text search
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS products USING fts5(
        name, 
        description
    )
    ''')

    # Insert sample data
    cursor.executemany('''
    INSERT INTO products (name, description) VALUES (?, ?)
    ''', [
        ('Laptop', 'High performance laptop for gaming and work'),
        ('Gaming Mouse', 'Ergonomic mouse with high DPI for precision'),
        ('Headphones', 'Noise-cancelling over-ear headphones with great sound quality'),
        ('Keyboard', 'Mechanical keyboard with RGB backlighting'),
        ('Smartphone', 'Latest model smartphone with high-resolution display'),
    ])

    conn.commit()
    conn.close()

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/search', methods=['GET'])
def search():
    """Search for products based on query string."""
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Search the FTS table using MATCH for full-text search
    cursor.execute('''
    SELECT name, description, rank FROM (
        SELECT name, description, rank(matchinfo(products)) as rank
        FROM products
        WHERE products MATCH ?
        ORDER BY rank DESC
    ) LIMIT 10
    ''', (query,))

    results = cursor.fetchall()
    conn.close()

    # Convert results to a list of dictionaries
    products = [{'name': row['name'], 'description': row['description']} for row in results]
    return jsonify(products)

if __name__ == '__main__':
    init_db()  # Initialize the database and tables
    app.run(debug=True)