#!/usr/bin/env python3
import sqlite3

def init_db(db_name=":memory:"):
    """
    Initialize the database by creating a products table and inserting sample data.
    """
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
    ''')
    # Insert some sample products
    sample_products = [
        ("Widget", "A useful widget for everyday tasks", 9.99),
        ("Gadget", "A fancy gadget with multiple features", 19.99),
        ("Doodad", "A small doodad that fits in your pocket", 4.99),
        ("Thingamajig", "An awesome thingamajig for tech enthusiasts", 29.99),
        ("Widget Pro", "An advanced widget with professional features", 14.99)
    ]
    c.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_products)
    conn.commit()
    return conn

def search_products(conn, name=None, description=None, price=None):
    """
    Search for products using optional filters:
      - name: case-insensitive substring match in the product name.
      - description: case-insensitive substring match in the product description.
      - price: finds products within ±5 units of the given price.
    
    A simple relevance metric is computed as follows:
      • +2 points if the 'name' filter is found in the product name.
      • +1 point if the 'description' filter is found in the product description.
      • Subtract the absolute difference between the product's price and the query price (if provided).
    
    This function uses parameterized queries to avoid SQL injection.
    """
    base_query = "SELECT id, name, description, price FROM products WHERE 1=1"
    params = []
    
    if name:
        base_query += " AND lower(name) LIKE ?"
        params.append(f"%{name.lower()}%")
    if description:
        base_query += " AND lower(description) LIKE ?"
        params.append(f"%{description.lower()}%")
    if price is not None:
        base_query += " AND price BETWEEN ? AND ?"
        params.extend([price - 5, price + 5])
    
    c = conn.cursor()
    c.execute(base_query, params)
    rows = c.fetchall()
    
    results = []
    for row in rows:
        prod_id, prod_name, prod_description, prod_price = row
        relevance = 0
        if name and name.lower() in prod_name.lower():
            relevance += 2
        if description and description.lower() in prod_description.lower():
            relevance += 1
        if price is not None:
            relevance -= abs(prod_price - price)
        results.append({
            "id": prod_id,
            "name": prod_name,
            "description": prod_description,
            "price": prod_price,
            "relevance": relevance
        })
    
    # Sort results by relevance (highest first)
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results

def main():
    conn = init_db()
    print("Database initialized with sample products.\n")
    
    # Test cases for the search functionality
    print("Test 1: Search by name 'widget'")
    results = search_products(conn, name="widget")
    for product in results:
        print(product)
    
    print("\nTest 2: Search by description 'fancy'")
    results = search_products(conn, description="fancy")
    for product in results:
        print(product)
    
    print("\nTest 3: Search by price near 10")
    results = search_products(conn, price=10)
    for product in results:
        print(product)
    
    print("\nTest 4: Search by name 'widget' and price near 15")
    results = search_products(conn, name="widget", price=15)
    for product in results:
        print(product)
    
    conn.close()

if __name__ == "__main__":
    main()
