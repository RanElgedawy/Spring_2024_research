import sqlite3
import sys

def create_db(conn):
    """
    Create the products table.
    """
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)
    conn.commit()

def insert_sample_products(conn):
    """
    Insert some sample products into the products table.
    """
    sample_data = [
        ("Wireless Mouse", "Ergonomic wireless mouse with USB receiver", 25.99),
        ("Mechanical Keyboard", "Backlit mechanical keyboard with blue switches", 79.99),
        ("USB-C Cable", "Durable USB-C to USB-A cable", 9.99),
        ("Gaming Monitor", "27-inch monitor with 144Hz refresh rate", 299.99),
        ("Laptop Stand", "Adjustable aluminum laptop stand", 39.99),
        ("Bluetooth Headphones", "Noise-cancelling over-ear headphones", 129.99),
        ("Smartphone Case", "Shock-absorbent case for smartphones", 19.99),
    ]
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO products (name, description, price)
        VALUES (?, ?, ?)
    """, sample_data)
    conn.commit()

def search_products(conn, query):
    """
    Search products by name, description, or price (if the query is numeric).
    Computes a relevance score based on:
      - +2 if the search text appears in the name.
      - +1 if it appears in the description.
      - +2 if the query is numeric and matches the price exactly.
    
    The function uses parameterized queries to avoid SQL injection.
    """
    cur = conn.cursor()
    
    # Prepare the search term for text matching
    search_term = f"%{query}%"
    
    try:
        # Check if query is numeric
        numeric_query = float(query)
        is_numeric = True
    except ValueError:
        is_numeric = False

    if is_numeric:
        # If numeric, include a price check
        sql = """
            SELECT id, name, description, price,
              ((CASE WHEN lower(name) LIKE lower(?) THEN 2 ELSE 0 END) +
               (CASE WHEN lower(description) LIKE lower(?) THEN 1 ELSE 0 END) +
               (CASE WHEN price = ? THEN 2 ELSE 0 END)) AS score
            FROM products
            WHERE lower(name) LIKE lower(?)
               OR lower(description) LIKE lower(?)
               OR price = ?
            ORDER BY score DESC, name
        """
        params = (search_term, search_term, numeric_query, search_term, search_term, numeric_query)
    else:
        sql = """
            SELECT id, name, description, price,
              ((CASE WHEN lower(name) LIKE lower(?) THEN 2 ELSE 0 END) +
               (CASE WHEN lower(description) LIKE lower(?) THEN 1 ELSE 0 END)) AS score
            FROM products
            WHERE lower(name) LIKE lower(?)
               OR lower(description) LIKE lower(?)
            ORDER BY score DESC, name
        """
        params = (search_term, search_term, search_term, search_term)
    
    cur.execute(sql, params)
    results = cur.fetchall()
    return results

def test_search(conn):
    """
    Test the search functionality in an interactive loop.
    """
    print("Product Search Test. Enter 'quit' to exit.")
    while True:
        query = input("\nEnter search query (name, description, or price): ").strip()
        if query.lower() in ('quit', 'exit'):
            print("Exiting test.")
            break
        results = search_products(conn, query)
        if results:
            print("\nSearch Results:")
            for row in results:
                # row: (id, name, description, price, score)
                print(f"ID: {row[0]}, Name: {row[1]}, Price: ${row[3]:.2f} (Score: {row[4]})")
                print(f"   Description: {row[2]}")
        else:
            print("No products found matching your query.")

def main():
    # Using an in-memory database for demonstration; change ':memory:' to a filename for persistence.
    conn = sqlite3.connect(":memory:")
    create_db(conn)
    insert_sample_products(conn)
    print("Database and sample products created.")
    
    # Run the interactive test
    test_search(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
