import sqlite3

def create_db():
    """
    Creates an in-memory SQLite database, defines the products table,
    and inserts some sample data.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)
    
    sample_products = [
        ("Basic T-Shirt", "A comfortable cotton t-shirt", 9.99),
        ("Designer Jeans", "Stylish and comfortable jeans", 49.99),
        ("Running Shoes", "Lightweight shoes for running", 79.99),
        ("Leather Jacket", "Genuine leather jacket", 199.99),
        ("Sports Watch", "Water resistant watch with GPS", 129.99),
        ("Summer Hat", "Lightweight hat for summer days", 19.99),
    ]
    
    conn.executemany(
        "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
        sample_products
    )
    conn.commit()
    return conn

def search_products(conn, name_search=None, description_search=None, price_min=None, price_max=None):
    """
    Searches for products using the given criteria.
    
    Parameters:
        conn: SQLite3 connection.
        name_search: Substring to match in the product name.
        description_search: Substring to match in the product description.
        price_min: Minimum price filter.
        price_max: Maximum price filter.
        
    Returns:
        List of tuples corresponding to matching products.
    """
    # Start with a base query that always evaluates true.
    query = "SELECT id, name, description, price FROM products WHERE 1=1"
    params = []
    
    # Add filters based on provided parameters.
    if name_search:
        query += " AND name LIKE ?"
        params.append(f"%{name_search}%")
    if description_search:
        query += " AND description LIKE ?"
        params.append(f"%{description_search}%")
    if price_min is not None:
        query += " AND price >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND price <= ?"
        params.append(price_max)
        
    # For demonstration, we order by price (you could add a relevance metric instead)
    query += " ORDER BY price ASC"
    
    cursor = conn.execute(query, params)
    results = cursor.fetchall()
    return results

def test_search_functionality():
    """
    Runs a series of test searches and prints the results.
    """
    conn = create_db()
    
    print("All products:")
    for row in search_products(conn):
        print(row)
    
    print("\nSearch for products with 'Watch' in the name:")
    for row in search_products(conn, name_search="Watch"):
        print(row)
    
    print("\nSearch for products with 'comfortable' in the description:")
    for row in search_products(conn, description_search="comfortable"):
        print(row)
    
    print("\nSearch for products priced between $20 and $150:")
    for row in search_products(conn, price_min=20, price_max=150):
        print(row)
    
    print("\nSearch for products with 'jeans' in the name and priced below $100:")
    for row in search_products(conn, name_search="jeans", price_max=100):
        print(row)
    
if __name__ == '__main__':
    test_search_functionality()
