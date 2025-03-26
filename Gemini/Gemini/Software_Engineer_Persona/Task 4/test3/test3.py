import sqlite3
import re

def create_search_table(db_name):
    """Creates a search table with category and price range columns."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS search_index")
    c.execute('''CREATE TABLE IF NOT EXISTS search_index
                 (id INTEGER PRIMARY KEY, product_id INTEGER, name TEXT, description TEXT, category TEXT, price REAL)''')
    conn.commit()
    conn.close()

def index_products(db_name, products_data):
    """Indexes products in the search table."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    for product in products_data:
        product_id = product['id']
        name = product['name']
        description = product['description']
        category = product.get('category', 'Unknown')  # Set a default category if missing
        price = product.get('price', 0.0)  # Set a default price if missing

        c.execute("INSERT INTO search_index VALUES (NULL, ?, ?, ?, ?, ?)", (product_id, name, description, category, price))

    conn.commit()
    conn.close()

def search_products(db_name, query, category=None, min_price=None, max_price=None):
    """Searches for products based on query, category, and price range."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Simple search based on full-text match
    query_terms = re.split(r'\s+', query)
    query_terms = [term for term in query_terms if term]

    if not query_terms:
        return "Please provide a search query"
    query_str = "SELECT product_id FROM search_index WHERE name LIKE ? OR description LIKE ?"
    query_args = ["%{}%".format(query_terms[0])] * 2  # Use only the first term for now

    # Add filters for category and price range
    conditions = []
    if category:
        conditions.append("category = ?")
        query_args.append(category)
    if min_price and max_price:
        conditions.append("price BETWEEN ? AND ?")
        query_args.extend([min_price, max_price])
    elif min_price:
        conditions.append("price >= ?")
        query_args.append(min_price)
    elif max_price:
        conditions.append("price <= ?")
        query_args.append(max_price)

    if conditions:
        query_str += " AND " + " AND ".join(conditions)

    # Check if query is empty
    if not query_terms:
        return "Please provide a search query."

    c.execute(query_str, query_args)
    results = c.fetchall()

    # Check if results are found
    if not results:
        return "No results found."

    conn.close()
    return results

products_data = [
    {'id': 1, 'name': 'Blue Jeans', 'description': 'Classic blue denim jeans.', 'category': 'Clothing', 'price': 59.99},
    {'id': 2, 'name': 'Black Jeans', 'description': 'denim.', 'category': 'Clothing', 'price': 129.99},
    {'id': 3, 'name': 'Running Shoes', 'description': 'Comfortable running shoes.', 'category': 'Footwear', 'price': 89.99},
    {'id': 4, 'name': 'Basketball', 'description': 'Official size basketball.', 'category': 'Sports Equipment', 'price': 24.99},
    # ... more products
]

index_products("ecommerce.db", products_data)

results = search_products("ecommerce.db", "denim")
print(results)

results = search_products("ecommerce.db", "clothing", category="Clothing")
print(results)

results = search_products("ecommerce.db", "shoes", min_price=50, max_price=100)
print(results)