from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL,
            stock INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create virtual table for full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
        USING fts5(name, description, content='products', content_rowid='id')
    ''')
    
    # Create triggers to maintain FTS index
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products
        BEGIN
            INSERT INTO products_fts(rowid, name, description)
            VALUES (new.id, new.name, new.description);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products
        BEGIN
            DELETE FROM products_fts WHERE rowid = old.id;
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products
        BEGIN
            DELETE FROM products_fts WHERE rowid = old.id;
            INSERT INTO products_fts(rowid, name, description)
            VALUES (new.id, new.name, new.description);
        END
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def test_form():
    # Simple HTML form for testing search
    return render_template_string('''
        <h1>Search Test</h1>
        <form action="/search">
            <input type="text" name="query" placeholder="Search...">
            <button type="submit">Search</button>
        </form>
        <p><a href="/populate">Add Test Data</a></p>
    ''')

@app.route('/populate', methods=['POST', 'GET'])
def populate_test_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM products')
    
    # Add test products
    test_products = [
        ('Men\'s Cotton T-Shirt', 'Comfortable cotton t-shirt for everyday wear', 19.99, 100),
        ('Wireless Bluetooth Headphones', 'Noise-cancelling headphones with premium sound', 149.99, 25),
        ('Stainless Steel Water Bottle', 'Eco-friendly 1L insulated water bottle', 29.95, 50),
        ('Running Shoes', 'Lightweight running shoes with breathable mesh', 89.99, 30),
        ('Leather Notebook', 'Handmade genuine leather journal', 24.50, 40),
    ]
    
    cursor.executemany('''
        INSERT INTO products (name, description, price, stock)
        VALUES (?, ?, ?, ?)
    ''', test_products)
    
    conn.commit()
    conn.close()
    return 'Added test products! <a href="/">Back to search</a>'

@app.route('/search')
def search_products():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Full-text search with ranking
    cursor.execute('''
        SELECT p.id, p.name, p.description, p.price, 
               bm25(products_fts) AS relevance
        FROM products_fts
        JOIN products p ON p.id = products_fts.rowid
        WHERE products_fts MATCH ?
        ORDER BY relevance
        LIMIT 20
    ''', (query,))
    
    results = [{
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'price': row[3],
        'relevance': row[4]
    } for row in cursor.fetchall()]
    
    conn.close()
    
    if request.accept_mimetypes.best == 'application/json':
        return jsonify(results)
    return render_template_string('''
        <h1>Search Results for "{{ query }}"</h1>
        <a href="/">Back to search</a>
        <ul>
        {% for product in results %}
            <li>
                <h3>{{ product.name }} (${{ "%.2f"|format(product.price) }})</h3>
                <p>{{ product.description }}</p>
                <em>Relevance score: {{ product.relevance }}</em>
            </li>
        {% else %}
            <li>No results found</li>
        {% endfor %}
        </ul>
    ''', query=query, results=results)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)