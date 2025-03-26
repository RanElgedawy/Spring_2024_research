import sqlite3
import re

def init_db(conn):
    """Create the products table and insert sample data."""
    cur = conn.cursor()
    # Create table
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Insert sample data (using parameterized queries)
    sample_products = [
        ("Red T-Shirt", "A bright red T-shirt made from 100% cotton.", 19.99),
        ("Blue Jeans", "Comfortable blue denim jeans with a classic fit.", 49.99),
        ("Wireless Mouse", "Ergonomic wireless mouse with adjustable DPI.", 25.50),
        ("Coffee Mug", "Ceramic coffee mug with a cool design.", 9.99),
        ("Laptop Sleeve", "Protective sleeve for 15-inch laptops.", 29.99)
    ]
    cur.executemany('''
        INSERT INTO products (name, description, price) VALUES (?, ?, ?)
    ''', sample_products)
    conn.commit()

def compute_score(product, query, query_num):
    """Compute a score for the product based on the query.
    
    - +2 points if the query appears in the name (case-insensitive)
    - +1 point if the query appears in the description (case-insensitive)
    - +3 points if the query is numeric and exactly matches the price
    """
    score = 0
    name = product["name"].lower()
    description = product["description"].lower() if product["description"] else ""
    
    # Use simple substring matching for name and description
    if query.lower() in name:
        score += 2
    if query.lower() in description:
        score += 1
    # If query is numeric, compare to price with a tolerance for floating point equality
    if query_num is not None:
        if abs(product["price"] - query_num) < 0.001:
            score += 3
    return score

def search_products(conn, query):
    """Search for products matching the query and return sorted results based on score."""
    cur = conn.cursor()
    # Fetch all products using a parameterized query (even though there is no user input here)
    cur.execute("SELECT id, name, description, price FROM products")
    rows = cur.fetchall()
    
    # Convert rows to dicts for easier handling
    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "price": row[3]
        })
    
    # Determine if query can be interpreted as a number
    query_num = None
    if re.fullmatch(r"\d+(\.\d+)?", query.strip()):
        query_num = float(query.strip())
    
    # Compute scores
    scored_products = []
    for prod in products:
        score = compute_score(prod, query, query_num)
        if score > 0:
            prod["score"] = score
            scored_products.append(prod)
    
    # Sort results by score descending
    scored_products.sort(key=lambda p: p["score"], reverse=True)
    return scored_products

def run_tests(conn):
    """Run test queries and display the results."""
    test_queries = [
        "red",
        "jeans",
        "mouse",
        "29.99",   # Should match Laptop Sleeve by price
        "mug",
        "cotton"
    ]
    for q in test_queries:
        print(f"\nSearch results for query: '{q}'")
        results = search_products(conn, q)
        if results:
            for prod in results:
                print(f"ID: {prod['id']} | Name: {prod['name']} | Price: {prod['price']} | Score: {prod['score']}")
        else:
            print("No matching products found.")

def main():
    # Using an in-memory database; change ':memory:' to a filename to persist data
    conn = sqlite3.connect(':memory:')
    # Enable accessing columns by name
    conn.row_factory = sqlite3.Row
    init_db(conn)
    
    print("=== Product Search Test ===")
    run_tests(conn)
    
    # Optionally, you could implement a simple interactive loop:
    while True:
        query = input("\nEnter a search query (or 'exit' to quit): ").strip()
        if query.lower() == 'exit':
            break
        results = search_products(conn, query)
        if results:
            print("Results:")
            for prod in results:
                print(f"ID: {prod['id']} | Name: {prod['name']} | Price: {prod['price']} | Score: {prod['score']}")
        else:
            print("No matching products found.")
    
    conn.close()

if __name__ == '__main__':
    main()
