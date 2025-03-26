import sqlite3

def setup_database():
    """Creates an in-memory SQLite database, a products table, and inserts sample data."""
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    
    # Create the products table
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)
    
    # Insert some sample products
    sample_data = [
        ("Laptop", "High performance laptop", 999.99),
        ("Smartphone", "Latest smartphone with an amazing camera", 699.99),
        ("Headphones", "Noise-cancelling headphones", 199.99),
        ("Keyboard", "Mechanical keyboard with RGB lighting", 89.99),
        ("Monitor", "27-inch 4K monitor", 349.99),
    ]
    
    c.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_data)
    conn.commit()
    return conn

def search_products(conn, search_term=None, min_price=None, max_price=None):
    """
    Searches for products based on an optional search_term (matched against name and description)
    and optional price filters (min_price and max_price). Uses a scoring metric to rank results.
    """
    c = conn.cursor()
    
    # Start building the query. If search_term is provided, compute a simple relevance score.
    query = "SELECT id, name, description, price"
    if search_term:
        query += """, 
            ((CASE WHEN lower(name) LIKE ? THEN 2 ELSE 0 END) +
             (CASE WHEN lower(description) LIKE ? THEN 1 ELSE 0 END)) as score"""
    query += " FROM products WHERE 1=1"
    
    # List of parameters for secure binding
    params = []
    
    # If search_term is provided, filter rows where the term appears in the name or description.
    if search_term:
        # Prepare the term for a case-insensitive search
        term = f"%{search_term.lower()}%"
        # For scoring purposes (name and description checks)
        params.extend([term, term])
        # Filter only rows that match at least in one field
        query += " AND (lower(name) LIKE ? OR lower(description) LIKE ?)"
        params.extend([term, term])
    
    # Apply price filters if provided
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    # Order the results: if a search term is provided, order by the computed score, then by price;
    # otherwise, simply order by price.
    if search_term:
        query += " ORDER BY score DESC, price ASC"
    else:
        query += " ORDER BY price ASC"
    
    c.execute(query, params)
    results = c.fetchall()
    return results

def test_search():
    """Sets up the DB, runs several search scenarios, and prints the results."""
    conn = setup_database()
    
    print("Search by term 'laptop':")
    results = search_products(conn, search_term="laptop")
    for row in results:
        print(row)
    
    print("\nSearch with price range 100 to 800:")
    results = search_products(conn, min_price=100, max_price=800)
    for row in results:
        print(row)
    
    print("\nSearch by term 'keyboard' and max price 100:")
    results = search_products(conn, search_term="keyboard", max_price=100)
    for row in results:
        print(row)
    
    conn.close()

if __name__ == "__main__":
    test_search()
