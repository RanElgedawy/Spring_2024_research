import sqlite3

def initialize_db(conn):
    """Creates the products table and inserts sample data."""
    cur = conn.cursor()
    # Create table if it doesn't exist
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    
    # Clear existing data for testing purposes
    cur.execute('DELETE FROM products')
    
    # Insert sample products
    sample_products = [
        ("Red T-shirt", "A comfortable red t-shirt", 19.99),
        ("Blue Jeans", "Stylish blue jeans", 49.99),
        ("Green Hat", "Green hat for sunny days", 15.99),
        ("Smartphone", "Latest model smartphone with excellent battery life", 699.99),
        ("Wireless Mouse", "Ergonomic wireless mouse", 29.99)
    ]
    cur.executemany('''
        INSERT INTO products (name, description, price)
        VALUES (?, ?, ?)
    ''', sample_products)
    conn.commit()

def search_products(conn, query=None, min_price=None, max_price=None):
    """
    Searches for products by matching the query against the product name and description.
    Additionally, you can filter by a minimum and/or maximum price.
    A simple relevance score is computed (name matches get 1 point and description matches get 0.5 points)
    and results are ordered by this score in descending order.
    
    :param conn: SQLite connection object.
    :param query: A text search query that will be used to match product name and description.
    :param min_price: Minimum price filter.
    :param max_price: Maximum price filter.
    :return: List of tuples representing the matching products along with their relevance score.
    """
    cur = conn.cursor()
    
    # Base query parts
    sql = """
        SELECT id, name, description, price,
               ((CASE WHEN name LIKE ? THEN 1 ELSE 0 END) +
                (CASE WHEN description LIKE ? THEN 0.5 ELSE 0 END)) AS relevance
        FROM products
        WHERE 1=1
    """
    params = []
    
    # If a query is provided, we look for it in name and description.
    # We use parameterized queries to protect against SQL injection.
    if query:
        like_query = f"%{query}%"
        params.extend([like_query, like_query])
    else:
        # If no text query is provided, add dummy values (that always return false)
        params.extend(["", ""])
    
    # Add price filters if provided
    if min_price is not None:
        sql += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)
        
    # Order by relevance score (higher scores first)
    sql += " ORDER BY relevance DESC"
    
    cur.execute(sql, params)
    return cur.fetchall()

def main():
    # Create an in-memory SQLite database (change to a filename for a persistent DB)
    conn = sqlite3.connect(":memory:")
    initialize_db(conn)
    
    print("Testing search function...\n")
    
    # Example 1: Search by a term that might match name/description
    term = "red"
    results = search_products(conn, query=term)
    print(f"Search results for query '{term}':")
    for row in results:
        print(row)
    print()
    
    # Example 2: Search by a term with price filter
    term = "wireless"
    results = search_products(conn, query=term, max_price=50)
    print(f"Search results for query '{term}' with max price 50:")
    for row in results:
        print(row)
    print()
    
    # Example 3: Search without a text query, just filtering by price range
    results = search_products(conn, min_price=20, max_price=100)
    print("Search results for products priced between 20 and 100 (no text query):")
    for row in results:
        print(row)
    print()
    
    # Close the connection when done
    conn.close()

if __name__ == "__main__":
    main()
