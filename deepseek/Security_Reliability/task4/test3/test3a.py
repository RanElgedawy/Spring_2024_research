import sqlite3
from sqlite3 import Error

# Database setup
def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to {db_file}, SQLite version: {sqlite3.version}")
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    """Create the products table if it doesn't exist."""
    try:
        sql_create_products_table = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        );
        """
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute(sql_create_products_table)
        print("Table 'products' created or already exists.")
    except Error as e:
        print(e)

def insert_sample_data(conn):
    """Insert sample data into the products table."""
    sample_products = [
        ("Laptop", "High-performance laptop with 16GB RAM", 1200.00),
        ("Smartphone", "Latest model with 128GB storage", 800.00),
        ("Tablet", "10-inch display, 64GB storage", 400.00),
        ("Headphones", "Noise-cancelling over-ear headphones", 250.00),
        ("Smartwatch", "Fitness tracking and heart rate monitor", 150.00),
    ]
    try:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", sample_products)
        conn.commit()
        print("Sample data inserted.")
    except Error as e:
        print(e)

# Search functionality
def search_products(conn, search_term=None, min_price=None, max_price=None):
    """
    Search for products based on name, description, or price range.
    :param conn: Database connection
    :param search_term: Term to search in name or description
    :param min_price: Minimum price for filtering
    :param max_price: Maximum price for filtering
    :return: List of matching products
    """
    try:
        cursor = conn.cursor()
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

        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(e)
        return []

# Testing the functionality
def test_search_functionality(conn):
    """Test the search functionality with various inputs."""
    print("\nTesting search functionality:")

    # Search by name
    print("\nSearch for 'laptop':")
    results = search_products(conn, search_term="laptop")
    for row in results:
        print(row)

    # Search by price range
    print("\nSearch for products between $100 and $500:")
    results = search_products(conn, min_price=100, max_price=500)
    for row in results:
        print(row)

    # Search by description
    print("\nSearch for 'storage' in description:")
    results = search_products(conn, search_term="storage")
    for row in results:
        print(row)

# Main function
def main():
    database = "ecommerce.db"

    # Create a database connection
    conn = create_connection(database)
    if conn is not None:
        # Create table and insert sample data
        create_table(conn)
        insert_sample_data(conn)

        # Test the search functionality
        test_search_functionality(conn)

        # Close the connection
        conn.close()
    else:
        print("Error: Cannot create database connection.")

if __name__ == "__main__":
    main()