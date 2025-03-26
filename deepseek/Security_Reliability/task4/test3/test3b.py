import sqlite3
from sqlite3 import Error

# Step 1: Database Setup
def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to {db_file}, SQLite version: {sqlite3.version}")
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    """Create a products table if it doesn't exist."""
    try:
        sql_create_products_table = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
        """
        conn.execute("DROP TABLE IF EXISTS products")
        conn.execute(sql_create_products_table)
        print("Products table created or already exists.")
    except Error as e:
        print(e)

def insert_sample_data(conn):
    """Insert sample data into the products table."""
    sample_products = [
        ("Laptop", "High-performance laptop with 16GB RAM", 1200.00),
        ("Smartphone", "Latest model with 128GB storage", 800.00),
        ("Headphones", "Noise-cancelling over-ear headphones", 250.00),
        ("Tablet", "10-inch tablet with stylus support", 600.00),
        ("Smartwatch", "Fitness tracking and heart rate monitoring", 200.00),
    ]
    try:
        conn.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_products)
        conn.commit()
        print("Sample data inserted.")
    except Error as e:
        print(e)

# Step 2: Secure Search Functionality
def search_products(conn, search_term=None, min_price=None, max_price=None):
    """
    Search for products based on name, description, or price range.
    Uses parameterized queries to prevent SQL injection.
    """
    try:
        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if search_term:
            query += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)

        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)

        cursor = conn.execute(query, params)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(e)
        return []

# Step 3: Test the Functionality
def test_search_functionality(conn):
    """Test the search functionality with various criteria."""
    print("\nTesting search functionality...")

    # Search by name or description
    print("\nSearch for 'phone':")
    results = search_products(conn, search_term="phone")
    for row in results:
        print(row)

    # Search by price range
    print("\nSearch for products between $500 and $1000:")
    results = search_products(conn, min_price=500, max_price=1000)
    for row in results:
        print(row)

    # Combined search
    print("\nSearch for 'smart' products under $300:")
    results = search_products(conn, search_term="smart", max_price=300)
    for row in results:
        print(row)

# Main Execution
if __name__ == "__main__":
    database = "ecommerce.db"

    # Create a database connection and set up the table
    conn = create_connection(database)
    if conn:
        create_table(conn)
        insert_sample_data(conn)

        # Test the search functionality
        test_search_functionality(conn)

        # Close the connection
        conn.close()