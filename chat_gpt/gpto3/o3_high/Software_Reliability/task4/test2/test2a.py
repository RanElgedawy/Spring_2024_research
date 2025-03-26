from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'products.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # enable column access by name
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = get_db_connection()
    cur = conn.cursor()
    sample_products = [
        ("Laptop", "A powerful laptop with 16GB RAM, 512GB SSD."),
        ("Smartphone", "A smartphone with a stunning display and fast processor."),
        ("Headphones", "Noise-cancelling headphones with rich sound quality."),
        ("Coffee Mug", "A mug for coffee lovers. Durable and stylish."),
        ("T-Shirt", "A comfortable cotton t-shirt available in multiple colors.")
    ]
    cur.executemany("INSERT INTO products (name, description) VALUES (?, ?)", sample_products)
    conn.commit()
    conn.close()

def compute_relevance(product, query_tokens):
    """
    Compute a simple relevance score for a product.
    For each token found in the name (weighted by 2) and in the description (weight 1),
    add to the product's score.
    """
    score = 0
    name = product["name"].lower()
    description = product["description"].lower()
    for token in query_tokens:
        score += 2 * name.count(token)
        score += description.count(token)
    return score

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    query_tokens = query.lower().split()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    conn.close()

    results = []
    for product in products:
        score = compute_relevance(product, query_tokens)
        if score > 0:
            results.append({
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "score": score
            })
    
    # sort the products by descending relevance score
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return jsonify({"results": results})

if __name__ == '__main__':
    # Set up the database and insert sample data for testing.
    create_tables()
    # Optional: clear previous data to avoid duplicates during testing.
    conn = get_db_connection()
    conn.execute("DELETE FROM products")
    conn.commit()
    conn.close()
    insert_sample_data()

    print("Server starting... To test, visit:")
    print("  http://127.0.0.1:5000/search?query=laptop")
    print("  http://127.0.0.1:5000/search?query=smartphone")
    app.run(debug=True)
