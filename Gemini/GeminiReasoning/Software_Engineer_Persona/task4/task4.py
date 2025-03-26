import sqlite3
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)

class ProductSearchEngine:
    def __init__(self, db_name='products.db'):
        self.db_name = db_name
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        conn = self._connect()
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
        # Add some sample data if the table is newly created or empty
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            self._insert_sample_data(cursor)
        conn.commit()
        conn.close()

    def _insert_sample_data(self, cursor):
        products = [
            ("Awesome T-Shirt", "A comfortable and stylish t-shirt made of 100% cotton.", 25.99),
            ("Cool Coffee Mug", "A ceramic mug perfect for your morning coffee or tea.", 12.50),
            ("Elegant Laptop Bag", "A professional and durable laptop bag with multiple compartments.", 79.99),
            ("Wireless Bluetooth Headphones", "High-quality wireless headphones with noise cancellation.", 149.00),
            ("Smartwatch Pro", "A feature-rich smartwatch to track your fitness and stay connected.", 299.00),
            ("Running Shoes", "Lightweight and comfortable running shoes for athletes.", 89.50),
            ("Leather Wallet", "A classic leather wallet with slots for cards and cash.", 45.00),
            ("Desk Lamp", "An adjustable desk lamp providing excellent lighting for your workspace.", 35.75),
            ("Gaming Mouse", "A high-precision gaming mouse with customizable buttons.", 59.99),
            ("Ergonomic Keyboard", "A comfortable ergonomic keyboard designed for long typing sessions.", 119.00),
            ("T-Shirt with Funny Print", "A humorous t-shirt with a unique graphic design.", 28.50),
            ("Coffee Grinder", "A burr coffee grinder for freshly ground coffee beans.", 65.00),
            ("Laptop Stand", "An adjustable laptop stand to improve your posture.", 29.99),
            ("Noise Cancelling Headphones", "Premium headphones with advanced noise cancellation technology.", 199.00),
            ("Fitness Tracker", "A wearable device to monitor your daily activity and sleep.", 79.99),
            ("Trail Running Shoes", "Durable running shoes designed for off-road trails.", 95.00),
            ("Card Holder Wallet", "A slim and minimalist wallet for carrying essential cards.", 22.00),
            ("Floor Lamp", "A stylish floor lamp to illuminate your living space.", 85.00),
            ("Wireless Mouse", "A convenient wireless mouse for everyday use.", 19.99),
            ("Mechanical Keyboard", "A tactile mechanical keyboard favored by programmers and gamers.", 149.00),
        ]
        cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)

    def search_products(self, query):
        conn = self._connect()
        cursor = conn.cursor()
        query_words = query.lower().split()
        results = []

        for word in query_words:
            # Simple search using LIKE operator for name and description
            cursor.execute("""
                SELECT id, name, description, price
                FROM products
                WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?
            """, ('%' + word + '%', '%' + word + '%'))

            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': row[3]
                })

        conn.close()
        return self._rank_results(results, query_words)

    def _rank_results(self, results, query_words):
        # Simple relevance ranking: count the number of query words found in name and description
        product_scores = defaultdict(int)
        product_details = {}

        for product in results:
            product_details[product['id']] = product
            name_lower = product['name'].lower()
            description_lower = (product['description'] or '').lower() # Handle cases where description might be None

            for word in query_words:
                if word in name_lower:
                    product_scores[product['id']] += 1
                if word in description_lower:
                    product_scores[product['id']] += 0.5 # Give description matches less weight

        ranked_results = sorted(product_scores.items(), key=lambda item: item[1], reverse=True)
        final_results = []
        seen_ids = set()
        for product_id, score in ranked_results:
            if product_id not in seen_ids:
                final_results.append(product_details[product_id])
                seen_ids.add(product_id)

        return final_results

search_engine = ProductSearchEngine()

@app.route('/api/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    if query:
        results = search_engine.search_products(query)
        if results:
            return jsonify({'results': results})
        else:
            return jsonify({'message': 'No results found'})
    else:
        return jsonify({'error': 'The "query" parameter is required.'}), 400

# --- Test the functionality (can be run directly) ---
if __name__ == "__main__":
    def test_search(query):
        print(f"\nSearching for (direct test): '{query}'")
        results = search_engine.search_products(query)
        if results:
            for product in results:
                print(f"  ID: {product['id']}")
                print(f"  Name: {product['name']}")
                print(f"  Description: {product['description']}")
                print(f"  Price: ${product['price']:.2f}")
                print("-" * 20)
        else:
            print("  No results found.")

    test_search("t-shirt")
    test_search("coffee mug")
    test_search("wireless headphones")
    test_search("laptop bag elegant")
    test_search("running shoes comfortable")
    test_search("funny print shirt")
    test_search("non-existent product")
    test_search("noise cancelling")
    test_search("keyboard")

    # To run the Flask API, uncomment the following line:
    app.run(debug=True)