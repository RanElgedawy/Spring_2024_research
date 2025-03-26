from flask import Flask, jsonify, request, g
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce2.db'

# Database setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        # Create products table
        db.execute("DROP TABLE IF EXISTS products")
        db.execute('''
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
        db.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
            USING fts5(name, description, content='products', content_rowid='id')
        ''')
        
        # Create triggers to maintain FTS index
        db.execute('''
            CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
                INSERT INTO products_fts(rowid, name, description)
                VALUES (new.id, new.name, new.description);
            END
        ''')
        
        db.execute('''
            CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, name, description)
                VALUES('delete', old.id, old.name, old.description);
            END
        ''')
        
        db.execute('''
            CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, name, description)
                VALUES('delete', old.id, old.name, old.description);
                INSERT INTO products_fts(rowid, name, description)
                VALUES (new.id, new.name, new.description);
            END
        ''')
        db.commit()

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.get_json()
    required_fields = ['name', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()
    try:
        cursor = db.execute('''
            INSERT INTO products (name, description, price, stock)
            VALUES (?, ?, ?, ?)
        ''', (
            data['name'],
            data.get('description', ''),
            data['price'],
            data.get('stock', 0)
        ))
        db.commit()
        return jsonify({'message': 'Product added', 'id': cursor.lastrowid}), 201
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_products():
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({'error': 'Missing search term'}), 400

    try:
        db = get_db()
        # Use FTS5 search with BM25 ranking
        query = '''
            SELECT 
                p.id,
                p.name,
                p.description,
                p.price,
                p.stock,
                fts.rank
            FROM products_fts fts
            JOIN products p ON fts.rowid = p.id
            WHERE fts MATCH ?
            ORDER BY fts.rank
            LIMIT 20
        '''
        results = db.execute(query, (search_term,)).fetchall()
        
        products = [dict(row) for row in results]
        # Remove rank from response if not needed
        for product in products:
            product.pop('rank', None)
            
        return jsonify({'count': len(products), 'results': products})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)