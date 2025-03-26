from flask import Flask, request, jsonify
import sqlite3
from typing import List, Tuple

class ProductSearchEngine:
    def __init__(self, db_name='products.db'):
        self.db_name = db_name
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def populate_data(self, products_data: List[Tuple[str, str, float]]):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO products (name, description, price)
            VALUES (?, ?, ?)
        """, products_data)
        conn.commit()
        conn.close()

    def search_products(self, query: str = None, min_price: float = None, max_price: float = None) -> List[Tuple[int, str, str, float, int]]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        sql_query = """
            SELECT id, name, description, price
            FROM products
            WHERE 1=1
        """
        params = []
        if query:
            sql_query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if min_price is not None:
            sql_query += " AND price >= ?"
            params.append(min_price)
        if max_price is not None:
            sql_query += " AND price <= ?"
            params.append(max_price)

        cursor.execute(sql_query, params)
        results = cursor.fetchall()
        conn.close()

        scored_results = []
        if query:
            query_lower = query.lower()
            for id, name, description, price in results:
                score = 0
                if query_lower in name.lower():
                    score += 3
                if description and query_lower in description.lower():
                    score += 1
                scored_results.append((id, name, description, price, score))
            scored_results.sort(key=lambda item: item[4], reverse=True)
        else:
            scored_results = [(id, name, description, price, 1) for id, name, description, price in results]

        return scored_results

# --- Flask API Implementation ---
app = Flask(__name__)
search_engine = ProductSearchEngine()

# Populate with some sample data (run this only once or when needed)
products = [
    ("Awesome T-Shirt", "A high-quality cotton t-shirt with a cool design.", 25.99),
    ("Comfortable Jeans", "Classic blue jeans made for everyday comfort.", 49.50),
    ("Stylish Sneaker", "Trendy sneakers for your active lifestyle.", 79.99),
    ("Awesome Coffee Mug", "A ceramic mug that keeps your coffee hot.", 12.75),
    ("Ergonomic Office Chair", "A chair designed for maximum comfort during long work hours.", 199.00),
    ("Cool T-Shirt", "A simple and cool t-shirt for casual wear.", 20.00),
]
search_engine.populate_data(products)

@app.route('/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    min_price_str = request.args.get('min_price')
    max_price_str = request.args.get('max_price')

    min_price = None
    if min_price_str:
        try:
            min_price = float(min_price_str)
        except ValueError:
            return jsonify({"error": "Invalid min_price value"}), 400

    max_price = None
    if max_price_str:
        try:
            max_price = float(max_price_str)
        except ValueError:
            return jsonify({"error": "Invalid max_price value"}), 400

    # Check if any arguments were provided
    if not query and min_price is None and max_price is None:
        return jsonify({"message": "Please provide search criteria (e.g., query, min_price, max_price)."}), 400

    results = search_engine.search_products(query=query, min_price=min_price, max_price=max_price)

    if results:
        # Format the results for JSON response
        formatted_results = []
        for id, name, description, price, score in results:
            formatted_results.append({
                "id": id,
                "name": name,
                "description": description,
                "price": price,
                "relevance_score": score
            })
        return jsonify(formatted_results)
    else:
        return jsonify({"message": "No results found."}), 200

if __name__ == '__main__':
    app.run(debug=True)