import sqlite3

# Create connection to the SQLite database
conn = sqlite3.connect(':memory:')  # Use an in-memory database for testing
cursor = conn.cursor()

# Step 1: Create the products table and FTS table
def create_tables():
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    );
    ''')
    
    # Create an FTS5 table for full-text search on name and description
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS product_fts USING fts5(name, description);
    ''')
    
    conn.commit()

# Step 2: Function to insert product data
def insert_product(name, description, price):
    cursor.execute('''
    INSERT INTO products (name, description, price)
    VALUES (?, ?, ?)
    ''', (name, description, price))
    
    # Insert into FTS table for full-text search
    cursor.execute('''
    INSERT INTO product_fts (name, description)
    VALUES (?, ?)
    ''', (name, description))
    
    conn.commit()

# Step 3: Secure search function with SQL parameterization and FTS
def search_products(query, min_price=None, max_price=None):
    base_query = '''
    SELECT p.id, p.name, p.description, p.price
    FROM products p
    JOIN product_fts fts ON p.name = fts.name
    WHERE fts.name MATCH ? OR fts.description MATCH ?
    '''
    params = [query, query]
    
    # Add price filters if provided
    if min_price is not None:
        base_query += " AND p.price >= ?"
        params.append(min_price)
    if max_price is not None:
        base_query += " AND p.price <= ?"
        params.append(max_price)
    
    cursor.execute(base_query, params)
    return cursor.fetchall()

# Step 4: Test data insertion and search functionality
def run_tests():
    # Create tables
    create_tables()

    # Insert sample products
    insert_product("Apple iPhone 12", "Latest model with 5G", 999.99)
    insert_product("Samsung Galaxy S21", "Flagship model with AMOLED display", 799.99)
    insert_product("Google Pixel 5", "Stock Android with great camera", 699.99)

    # Perform searches
    print("Search for 'Apple':")
    results = search_products('Apple')
    for result in results:
        print(result)

    print("\nSearch for 'Android' with price filter:")
    results = search_products('Android', min_price=600, max_price=800)
    for result in results:
        print(result)

# Run the test
run_tests()

# Close the connection when done
conn.close()