from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)

DATABASE = 'ecommerce.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Manually added this code to prevent conflicts with already existing tables
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        ''')
        db.commit()

def insert_sample_data():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        sample_data = [
            ('Laptop', 'Powerful laptop for all your needs'),
            ('Smartphone', 'Latest smartphone with great features'),
            ('Headphones', 'High-quality headphones for immersive sound experience')
        ]
        cursor.executemany('INSERT INTO products (name, description) VALUES (?, ?)', sample_data)
        db.commit()

@app.route('/search')
def search():
    search_term = request.args.get('query')
    if not search_term:
        return jsonify({'error': 'Query parameter "query" is missing.'}), 400
    
    db = get_db()
    cursor = db.cursor()
    query = '%' + search_term + '%'  # Wildcard for partial matching
    cursor.execute('''
        SELECT id, name, description
        FROM products
        WHERE name LIKE ? OR description LIKE ?
    ''', (query, query))
    results = cursor.fetchall()

    if results:
        response = [{'id': result['id'], 'name': result['name'], 'description': result['description']} for result in results]
        return jsonify(response)
    else:
        return jsonify({'message': 'No results found.'})

if __name__ == '__main__':
    init_db()  # Initialize database schema
    insert_sample_data()  # Insert sample data
    app.run(debug=True)