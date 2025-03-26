import sqlite3
from sqlite3 import Error

# Database initialization
def create_connection():
    """Create a database connection to an in-memory SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(':memory:')
        print(f"Connected to SQLite version {sqlite3.version}")
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables(conn):
    """Create products table"""
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        ''')
        conn.commit()
    except Error as e:
        print(e)

# Test data insertion
def insert_test_data(conn):
    """Insert sample products for testing"""
    products = [
        ('Laptop', 'High-performance laptop with 16GB RAM', 999.99),
        ('Smartphone', 'Latest model with 5G connectivity', 699.99),
        ('Tablet', '10-inch portable device with stylus', 299.99),
        ('Headphones', 'Noise-cancelling wireless headphones', 199.99),
        ('Camera', '4K mirrorless camera with lens kit', 1299.99)
    ]
    
    try:
        c = conn.cursor()
        c.executemany('''
            INSERT INTO products (name, description, price)
            VALUES (?, ?, ?)
        ''', products)
        conn.commit()
        print("Inserted test data successfully")
    except Error as e:
        print(f"Error inserting test data: {e}")

# Secure search implementation
def search_products(conn, search_params):
    """
    Secure product search with dynamic filters
    Returns results ordered by relevance (number of matched criteria)
    """
    conditions = []
    params = []
    relevance = []
    
    # Build search conditions and parameters
    if 'name' in search_params:
        conditions.append("name LIKE ?")
        relevance.append("(name LIKE ?)")
        params.append(f"%{search_params['name']}%")
    
    if 'description' in search_params:
        conditions.append("description LIKE ?")
        relevance.append("(description LIKE ?)")
        params.append(f"%{search_params['description']}%")
    
    if 'price' in search_params:
        conditions.append("price = ?")
        relevance.append("(price = ?)")
        params.append(float(search_params['price']))
    
    # Build SQL query with parameterized inputs
    where_clause = " OR ".join(conditions) if conditions else "1=1"
    relevance_score = " + ".join(relevance) if relevance else "0"
    
    query = f"""
        SELECT *, ({relevance_score}) AS relevance
        FROM products
        WHERE {where_clause}
        ORDER BY relevance DESC, name ASC
    """
    
    try:
        c = conn.cursor()
        # Pass parameters twice: once for relevance calculation and once for WHERE clause
        c.execute(query, params + params.copy())
        return c.fetchall()
    except Error as e:
        print(f"Search error: {e}")
        return []

# Test functionality
def test_search(conn):
    """Interactive test function"""
    print("\nTest Product Search")
    print("-------------------")
    
    search_params = {}
    if name := input("Product name (partial match, leave blank to skip): ").strip():
        search_params['name'] = name
    if desc := input("Description (partial match, leave blank to skip): ").strip():
        search_params['description'] = desc
    if price := input("Exact price (numbers only, leave blank to skip): ").strip():
        search_params['price'] = price
    
    results = search_products(conn, search_params)
    
    if not results:
        print("\nNo matching products found")
        return
    
    print("\nSearch Results (ordered by relevance):")
    print(f"{'ID':<4} {'Name':<12} {'Price':<8} {'Relevance':<9} Description")
    for product in results:
        print(f"{product[0]:<4} {product[1]:<12} ${product[3]:<7.2f} {product[4]:<9} {product[2]}")

# Main execution
if __name__ == "__main__":
    db_conn = create_connection()
    if db_conn:
        create_tables(db_conn)
        insert_test_data(db_conn)
        
        # Run test interface
        while True:
            test_search(db_conn)
            if input("\nPerform another search? (y/n): ").lower() != 'y':
                break
        
        db_conn.close()
        print("Database connection closed")