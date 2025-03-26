import sqlite3

def initialize_db(conn):
    """
    Creates the products table and inserts sample data.
    """
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Sample products for testing
    sample_products = [
        ('Red T-shirt', 'A bright red t-shirt made of cotton.', 19.99),
        ('Blue Jeans', 'Comfortable blue jeans with a classic fit.', 49.99),
        ('Green Hat', 'Stylish green hat for summer.', 15.99),
        ('Yellow Jacket', 'Water-resistant yellow jacket, perfect for rainy days.', 89.99),
        ('Black Shoes', 'Elegant black shoes for formal occasions.', 129.99)
    ]
    cur.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', sample_products)
    conn.commit()

def search_products(conn, search_text=None, min_price=None, max_price=None):
    """
    Searches for products using secure parameterized queries.
    
    If search_text is provided, a simple ranking metric is computed:
      - +10 points if the search term is found in the product name (case-insensitive)
      - +5 points if found in the product description
      
    Products are then ordered by the computed score (and by price if scores are equal).
    """
    cur = conn.cursor()
    params = []
    
    # Build SELECT clause: include a score only if search_text is provided.
    if search_text:
        # Use wildcards to enable partial matching.
        like_param = f"%{search_text.lower()}%"
        select_clause = ("(CASE WHEN lower(name) LIKE ? THEN 10 ELSE 0 END + "
                         "CASE WHEN lower(description) LIKE ? THEN 5 ELSE 0 END) as score")
        params.extend([like_param, like_param])
        where_clause = " AND (lower(name) LIKE ? OR lower(description) LIKE ?)"
        params.extend([like_param, like_param])
    else:
        select_clause = "0 as score"
        where_clause = ""
    
    # Build the main query with optional price filters.
    query = f"SELECT id, name, description, price, {select_clause} FROM products WHERE 1=1{where_clause}"
    
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    # Order by score (if search_text is provided) and then by price.
    if search_text:
        query += " ORDER BY score DESC, price ASC"
    else:
        query += " ORDER BY price ASC"
    
    cur.execute(query, params)
    return cur.fetchall()

def main():
    # Use an in-memory SQLite database for testing.
    conn = sqlite3.connect(':memory:')
    initialize_db(conn)
    
    print("=== Product Search ===")
    print("Enter search criteria (leave blank to skip a filter).")
    search_text = input("Search text (name/description): ").strip() or None
    min_price_input = input("Minimum price: ").strip()
    max_price_input = input("Maximum price: ").strip()
    
    min_price = float(min_price_input) if min_price_input else None
    max_price = float(max_price_input) if max_price_input else None
    
    results = search_products(conn, search_text, min_price, max_price)
    
    if results:
        print("\n--- Search Results ---")
        for prod in results:
            prod_id, name, description, price, score = prod
            print(f"ID: {prod_id} | Name: {name} | Price: ${price:.2f} | Score: {score}")
            print(f"Description: {description}")
            print("-" * 40)
    else:
        print("No products found matching the criteria.")
    
    conn.close()

if __name__ == "__main__":
    main()
