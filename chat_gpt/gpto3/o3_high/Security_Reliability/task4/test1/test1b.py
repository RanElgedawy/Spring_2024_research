import sqlite3

def create_database():
    """
    Creates an in-memory SQLite database, a 'products' table,
    and inserts some sample products.
    """
    conn = sqlite3.connect(":memory:")  # use an in-memory DB for testing
    c = conn.cursor()
    # Create the products table
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Sample product data: (name, description, price)
    products = [
        ("Widget", "A useful widget", 19.99),
        ("Gadget", "A fancy gadget", 29.99),
        ("Thingamajig", "An interesting thingamajig", 9.99),
        ("Doohickey", "A doohickey for every need", 14.99),
        ("Contraption", "A complex contraption", 49.99),
    ]
    # Use parameterized queries to insert data safely
    c.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)
    conn.commit()
    return conn

def search_products(conn, search_term=None, price_min=0, price_max=1e9):
    """
    Searches for products that satisfy the given criteria.
    
    - search_term: if provided, the term is searched for in both the name and description.
    - price_min and price_max: filter products based on price.
    
    The query uses parameterized statements to avoid SQL injection.
    Additionally, if a search term is provided, a simple relevance score is calculated:
      - 2 points if the term appears in the product name,
      - 1 point if it appears in the description.
      
    The results are ordered by this score in descending order.
    """
    c = conn.cursor()
    
    # Base query and parameters for price filtering.
    query = "SELECT id, name, description, price"
    params = []
    
    if search_term:
        # Add a computed relevance score column.
        query += ", ((CASE WHEN name LIKE ? THEN 2 ELSE 0 END) + " \
                 "(CASE WHEN description LIKE ? THEN 1 ELSE 0 END)) AS score "
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term])
    
    query += " FROM products WHERE price >= ? AND price <= ?"
    params.extend([price_min, price_max])
    
    if search_term:
        # Limit results to those where the search term appears in name or description.
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([like_term, like_term])
        query += " ORDER BY score DESC"
    
    # Execute the query using parameterized inputs to prevent SQL injection.
    c.execute(query, params)
    return c.fetchall()

def test_search():
    """
    Creates the database and performs a series of test searches.
    """
    conn = create_database()
    
    print("Test 1: Search for 'widget'")
    results = search_products(conn, search_term="widget")
    for r in results:
        print(r)
    
    print("\nTest 2: Search for products with price between 10 and 30")
    results = search_products(conn, price_min=10, price_max=30)
    for r in results:
        print(r)
    
    print("\nTest 3: Search for 'gadget' with price between 20 and 40")
    results = search_products(conn, search_term="gadget", price_min=20, price_max=40)
    for r in results:
        print(r)
    
    conn.close()

if __name__ == "__main__":
    test_search()
