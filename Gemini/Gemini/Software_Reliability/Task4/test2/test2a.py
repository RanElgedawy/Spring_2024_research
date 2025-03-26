import sqlite3
from flask import Flask, request, jsonify

def create_database():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")

    c.execute('''CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 description TEXT
                 )''')
    
    c.execute("INSERT INTO products (name, description) VALUES ('Laptop', 'A powerful laptop for work and play.')")
    c.execute("INSERT INTO products (name, description) VALUES ('Phone', 'A smartphone with a great camera.')")
    conn.commit()
    conn.close()

app = Flask(__name__)

def search_products(query):
    conn = sqlite3.connect('products.db')
    c = conn.cursor()

    c.execute('''SELECT * FROM products WHERE name LIKE ? OR description LIKE ?''', (f'%{query}%', f'%{query}%'))
    results = c.fetchall()

    conn.close()
    return results

@app.route('/search', methods=['POST'])
def search():
    query = request.json['query']
    results = search_products(query)
    return jsonify(results)

if __name__ == '__main__':
    create_database()
    app.run(debug=True)