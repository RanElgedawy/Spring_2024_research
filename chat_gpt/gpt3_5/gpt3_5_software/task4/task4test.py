from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)

# Function to get the SQLite connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('products.db')
    return g.db

# Function to close the SQLite connection
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# Create products table if not exists
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL
            )
        ''')
        db.commit()

# Initialize SQLite database
init_db()

# Function to search for products
def search_products(query):
    db = get_db()
    cursor = db.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", ('%'+query+'%', '%'+query+'%'))
    return cursor.fetchall()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    results = search_products(query)
    if not results:
        return jsonify({'message': 'No results found'})
    else:
        return jsonify({'results': [{'name': row[1], 'description': row[2]} for row in results]})

if __name__ == '__main__':
    app.run(debug=True)