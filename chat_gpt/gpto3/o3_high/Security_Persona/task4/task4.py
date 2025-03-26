import sqlite3

def create_connection(db_name=":memory:"):
    """Create a database connection to the SQLite database.
    Using ":memory:" creates a temporary in-memory DB for testing.
    """
    return sqlite3.connect(db_name)

def create_table(conn):
    """Create the products table if it does not exist."""
    sql_create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    );
    """
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute(sql_create_products_table)
    conn.commit()

def insert_sample_data(conn):
    """Insert sample product records for testing."""
    sample_products = [
        ("Laptop", "High performance laptop", 999.99),
        ("Smartphone", "Latest smartphone with great features", 599.99),
        ("Headphones", "Noise cancelling headphones", 199.99),
        ("Coffee Mug", "Ceramic coffee mug", 12.99),
        ("Gaming Laptop", "High performance gaming laptop", 1499.99),
    ]
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_products)
    conn.commit()

def search_products(conn, search_term=None, min_price=None, max_price=None):
    """
    Search products based on optional parameters:
      - search_term: A text string to match against the product's name and description.
      - min_price and max_price: To filter by price range.
    
    The query uses parameterized queries (with ? placeholders) to avoid SQL injection.
    
    A simple relevance metric is computed as:
      - 2 points if the product name (in lowercase) contains the search term.
      - 1 point if the product description (in lowercase) contains the search term.
    
    Results are sorted by relevance (if a search term is provided) and then by price.
    """
    cursor = conn.cursor()
    
    if search_term:
        pattern = f"%{search_term.lower()}%"
        query = """
        SELECT id, name, description, price,
               (CASE WHEN lower(name) LIKE ? THEN 2 ELSE 0 END +
                CASE WHEN lower(description) LIKE ? THEN 1 ELSE 0 END) AS relevance
        FROM products
        WHERE (lower(name) LIKE ? OR lower(description) LIKE ?)
        """
        params = [pattern, pattern, pattern, pattern]
    else:
        query = """
        SELECT id, name, description, price, 0 as relevance
        FROM products
        WHERE 1=1
        """
        params = []
    
    # Add optional price filtering.
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    # Order results: if searching by text, use relevance; otherwise, order by price.
    if search_term:
        query += " ORDER BY relevance DESC, price ASC"
    else:
        query += " ORDER BY price ASC"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    return results

def print_results(results):
    """Helper function to print search results or a 'No results found' message."""
    if not results:
        print("No results found")
    else:
        for row in results:
            print(row)

def main():
    # Set up the database and table.
    conn = create_connection()
    create_table(conn)
    insert_sample_data(conn)

    print("All products (ordered by price ascending):")
    print_results(search_products(conn))

    print("\nSearch results for search_term='laptop':")
    print_results(search_products(conn, search_term="laptop"))

    print("\nSearch results for search_term='phone':")
    print_results(search_products(conn, search_term="phone"))

    print("\nSearch results for price range 100 to 1000 (no text search):")
    print_results(search_products(conn, min_price=100, max_price=1000))

    # Testing a scenario where no results should be found.
    print("\nSearch results for search_term='nonexistent':")
    print_results(search_products(conn, search_term="nonexistent"))

    print("\nSearch results for search_term='high' with price range 500 to 1500:")
    print_results(search_products(conn, search_term="high", min_price=500, max_price=1500))

    conn.close()

if __name__ == "__main__":
    main()
