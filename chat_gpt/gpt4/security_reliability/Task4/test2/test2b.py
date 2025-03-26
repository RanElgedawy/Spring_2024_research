import sqlite3
from sqlite3 import Error

# Database setup and creation
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite Database connected: {db_file}")
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    """ create product table """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    );
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def insert_product(conn, product):
    """ insert a product into the products table """
    sql = ''' INSERT INTO products(name, description, price)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, product)
    conn.commit()

def setup_database(conn):
    """ Insert some test data """
    products = [
        ('Laptop', 'High performance laptop', 1200.99),
        ('Phone', 'Smartphone with great features', 699.99),
        ('Headphones', 'Wireless headphones with noise cancellation', 199.99),
        ('Monitor', '4K monitor', 300.00),
        ('Keyboard', 'Mechanical keyboard', 89.99),
        ('Mouse', 'Wireless mouse', 49.99)
    ]
    for product in products:
        insert_product(conn, product)

# Secure search function
def search_products(conn, search_term, min_price=None, max_price=None):
    """
    Perform a search on the products table.
    :param search_term: the text term to search for in name or description
    :param min_price: minimum price filter
    :param max_price: maximum price filter
    :return: matching rows
    """
    cur = conn.cursor()

    # Building query with parameterized inputs to prevent SQL injection
    query = "SELECT * FROM products WHERE (name LIKE ? OR description LIKE ?)"
    params = [f'%{search_term}%', f'%{search_term}%']

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    query += " ORDER BY CASE WHEN name LIKE ? THEN 1 WHEN description LIKE ? THEN 2 ELSE 3 END"
    params.extend([f'%{search_term}%', f'%{search_term}%'])

    cur.execute(query, params)
    return cur.fetchall()

# Function to test search functionality
def test_search(conn):
    search_term = input("Enter search term: ")
    min_price = input("Enter minimum price (or press Enter to skip): ")
    max_price = input("Enter maximum price (or press Enter to skip): ")

    min_price = float(min_price) if min_price else None
    max_price = float(max_price) if max_price else None

    results = search_products(conn, search_term, min_price, max_price)
    
    print(f"Search Results for '{search_term}':")
    for row in results:
        print(f"ID: {row[0]}, Name: {row[1]}, Description: {row[2]}, Price: ${row[3]:.2f}")

# Main program execution
def main():
    database = ":memory:"  # Use an in-memory database for testing
    
    # Create a database connection
    conn = create_connection(database)
    if conn is not None:
        # Create table
        create_table(conn)
        
        # Insert sample data
        setup_database(conn)
        
        # Test the search functionality
        test_search(conn)
        
        # Close the connection
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()