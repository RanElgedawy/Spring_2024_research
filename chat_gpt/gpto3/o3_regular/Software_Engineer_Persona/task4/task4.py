from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def create_connection():
    # For demonstration, we use an in‑memory SQLite DB.
    # Note: In‑memory DBs are not persistent and are not ideal for production.
    return sqlite3.connect(":memory:", check_same_thread=False)

conn = create_connection()

def create_tables(conn):
    cursor = conn.cursor()
    # Create a products table.
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    # Create a full-text search virtual table using FTS5.
    cursor.execute("DROP TABLE IF EXISTS product_search")
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS product_search 
        USING fts5(name, description, content='products', content_rowid='id')
    ''')
    conn.commit()

def populate_data(conn):
    # Sample product data.
    products = [
        ('Apple iPhone 12', 'The latest iPhone with advanced features and a sleek design.'),
        ('Samsung Galaxy S21', 'Experience the new Galaxy with a stunning display and top performance.'),
        ('Google Pixel 5', 'The ultimate Google phone with an exceptional camera and pure Android experience.'),
        ('Dell XPS 13', 'A powerful and sleek laptop ideal for professionals and creatives alike.'),
        ('Apple MacBook Pro', 'The best laptop for creatives and professionals, featuring high performance and stunning visuals.')
    ]
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO products (name, description) VALUES (?, ?)', products)
    conn.commit()
    # Populate the FTS virtual table.
    cursor.execute('''
        INSERT INTO product_search (rowid, name, description)
        SELECT id, name, description FROM products
    ''')
    conn.commit()

# Initialize the database.
create_tables(conn)
populate_data(conn)

def search_products(conn, query):
    cursor = conn.cursor()
    # Perform a full‑text search using SQLite's FTS5 and BM25 for relevance.
    cursor.execute('''
        SELECT p.id, p.name, p.description, bm25(product_search) AS score
        FROM product_search
        JOIN products p ON p.id = product_search.rowid
        WHERE product_search MATCH ?
        ORDER BY score ASC
    ''', (query,))
    return cursor.fetchall()

@app.route('/search', methods=['GET'])
def search_api():
    # Check if the required query argument is provided.
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing required "query" parameter.'}), 400

    results = search_products(conn, query)
    if not results:
        return jsonify({'message': 'No results found.'}), 200

    # Format results for JSON response.
    products_list = []
    for product_id, name, description, score in results:
        products_list.append({
            'id': product_id,
            'name': name,
            'description': description,
            'score': score
        })

    return jsonify({'results': products_list}), 200

if __name__ == '__main__':
    app.run(debug=True)
