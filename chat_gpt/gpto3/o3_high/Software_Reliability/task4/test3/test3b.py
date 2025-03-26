import sqlite3

def create_database():
    """Creates an in-memory SQLite DB with a products table and sample data."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    # Sample products for testing
    products = [
        ("Apple iPhone 14", "Latest smartphone from Apple with advanced features"),
        ("Samsung Galaxy S22", "High performance Android smartphone with sleek design"),
        ("Dell XPS 15", "Powerful laptop for professionals"),
        ("Apple MacBook Pro", "High-end laptop with impressive display"),
        ("Sony WH-1000XM4", "Noise-cancelling wireless headphones with superb sound quality"),
        ("Logitech MX Master 3", "Advanced wireless mouse with ergonomic design"),
    ]
    cursor.executemany('INSERT INTO products (name, description) VALUES (?, ?)', products)
    conn.commit()
    return conn

def search_products(conn, query):
    """
    Searches for products matching the query in either the name or description.
    The relevance metric is computed as:
      score = (occurrences_in_name * 2) + (occurrences_in_description * 1)
    where the occurrence count is calculated via the difference in string lengths.
    """
    cursor = conn.cursor()
    # Convert query to lowercase for case-insensitive matching.
    query_lower = query.lower()
    # SQL to compute occurrence counts and rank by relevance.
    sql = '''
    SELECT id, name, description,
           (
               ((LENGTH(LOWER(name)) - LENGTH(REPLACE(LOWER(name), ?, ''))) / LENGTH(?)) * 2 +
               ((LENGTH(LOWER(description)) - LENGTH(REPLACE(LOWER(description), ?, ''))) / LENGTH(?))
           ) as score
    FROM products
    WHERE LOWER(name) LIKE '%' || ? || '%' OR LOWER(description) LIKE '%' || ? || '%'
    ORDER BY score DESC
    '''
    # All parameters use the lower-cased query.
    params = (query_lower, query_lower, query_lower, query_lower, query_lower, query_lower)
    cursor.execute(sql, params)
    results = cursor.fetchall()
    return results

def test_search():
    """Runs test queries and prints the results."""
    conn = create_database()
    test_queries = ["apple", "laptop", "wireless", "smartphone"]
    for q in test_queries:
        print(f"Results for '{q}':")
        results = search_products(conn, q)
        if results:
            for row in results:
                # row[3] is the computed score.
                print(f"ID: {row[0]}, Name: {row[1]}, Score: {row[3]}")
        else:
            print("No results found.")
        print("-" * 40)

if __name__ == '__main__':
    test_search()
