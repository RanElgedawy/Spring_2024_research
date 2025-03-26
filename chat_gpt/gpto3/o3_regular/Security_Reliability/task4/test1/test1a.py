import sqlite3
import re

def create_connection(db_file=":memory:"):
    """Create a database connection to a SQLite database (in memory by default)."""
    conn = sqlite3.connect(db_file)
    return conn

def setup_database(conn):
    """Create the products table and insert sample data."""
    cursor = conn.cursor()
    # Create table
    cursor.execute("DROP TABLE IF EXISTS products")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL
        )
    """)
    # Insert sample products
    sample_products = [
        ("Widget Pro", "High quality widget with extra features", 19.99),
        ("Widget Basic", "Affordable widget for everyday use", 9.99),
        ("Gadget", "A useful gadget for multiple purposes", 14.99),
        ("Super Gadget", "Premium gadget with advanced capabilities", 29.99),
        ("Budget Widget", "Cost-effective widget option", 4.99),
    ]
    cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_products)
    conn.commit()

def fetch_all_products(conn):
    """Retrieve all products from the database securely."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price FROM products")
    return cursor.fetchall()

def search_products(conn, query):
    """
    Search for products by matching the query against the name, description, and price.
    A custom ranking metric is applied:
      - +3 points if the query (case-insensitive) appears in the product name.
      - +1 point if it appears in the product description.
      - +5 points if the query exactly matches the price (if query is numeric).
    Returns a sorted list of matching products based on their score.
    """
    products = fetch_all_products(conn)
    results = []
    
    # Check if query is a number (for price matching)
    try:
        query_price = float(query)
    except ValueError:
        query_price = None

    # Normalize query for text matching
    norm_query = query.lower()

    for prod in products:
        prod_id, name, description, price = prod
        score = 0
        
        # Check for name match (case-insensitive)
        if norm_query in name.lower():
            score += 3
        
        # Check for description match
        if description and norm_query in description.lower():
            score += 1
        
        # Check for an exact price match (if the query is numeric)
        if query_price is not None and abs(price - query_price) < 1e-2:
            score += 5

        # Only include product if there is some match
        if score > 0:
            results.append((score, prod))

    # Sort results by score in descending order; higher score means a better match.
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Extract just the product details for output
    return [prod for score, prod in results]

def main():
    conn = create_connection()
    setup_database(conn)
    
    # Provide a way to test the functionality
    print("Enter your search query (for example: 'widget', '9.99', or 'gadget'):")
    query = input("> ").strip()
    
    results = search_products(conn, query)
    if results:
        print("\nSearch results:")
        for prod in results:
            prod_id, name, description, price = prod
            print(f"ID: {prod_id} | Name: {name} | Description: {description} | Price: ${price:.2f}")
    else:
        print("No products match your search query.")

if __name__ == '__main__':
    main()
