import sqlite3

def create_connection():
    # Create a connection to an in-memory SQLite database.
    # For production, you might use a file-based DB.
    return sqlite3.connect(":memory:")

def create_table(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
    ''')
    conn.commit()

def insert_sample_data(conn):
    products = [
        ("Widget", "A useful widget", 19.99),
        ("Gadget", "A fancy gadget", 29.99),
        ("Thingamajig", "An interesting thingamajig", 9.99),
        ("Doodad", "A small doodad", 4.99),
        ("Contraption", "An innovative contraption", 49.99)
    ]
    cur = conn.cursor()
    # Use parameterized queries to insert sample data safely.
    cur.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products)
    conn.commit()

def search_products(conn, search_term=None, min_price=None, max_price=None):
    """
    Searches for products by keyword in the name and description,
    and optionally filters by a minimum and/or maximum price.
    """
    cur = conn.cursor()
    query = "SELECT id, name, description, price FROM products WHERE 1=1"
    params = []
    
    # If a search term is provided, search within the name and description fields.
    if search_term:
        query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)"
        # Use wildcards for partial matching.
        term = f"%{search_term.lower()}%"
        params.extend([term, term])
    
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    # Ordering by price ascending as an example metric.
    query += " ORDER BY price ASC"
    
    cur.execute(query, params)
    return cur.fetchall()

def test_search(conn):
    print("Test the product search functionality")
    search_term = input("Enter a keyword to search in name/description (or leave blank): ").strip()
    min_price_input = input("Enter minimum price (or leave blank): ").strip()
    max_price_input = input("Enter maximum price (or leave blank): ").strip()

    min_price = float(min_price_input) if min_price_input else None
    max_price = float(max_price_input) if max_price_input else None

    results = search_products(conn, search_term if search_term else None, min_price, max_price)
    
    print("\nSearch Results:")
    if results:
        for product in results:
            print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}, Price: {product[3]}")
    else:
        print("No products found matching your criteria.")

def main():
    conn = create_connection()
    create_table(conn)
    insert_sample_data(conn)
    test_search(conn)
    conn.close()

if __name__ == "__main__":
    main()
