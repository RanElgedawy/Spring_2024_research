import sqlite3

def create_connection():
    # Create an in-memory SQLite database.
    conn = sqlite3.connect(':memory:')
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_description TEXT NOT NULL
        );
    ''')
    conn.commit()

def insert_sample_data(conn):
    # Insert sample products into the database.
    products = [
        ('Apple iPhone 13', 'Latest model of the iPhone with A15 chip.'),
        ('Samsung Galaxy S21', 'High-end Android smartphone with great camera features.'),
        ('Sony Headphones', 'Noise-cancelling over-ear headphones with superb sound quality.'),
        ('Dell XPS 15 Laptop', 'Powerful laptop with high-resolution display for professionals.'),
        ('Apple MacBook Pro', 'Professional laptop featuring the M1 chip and Retina display.'),
    ]
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO products (product_name, product_description) VALUES (?, ?)
    ''', products)
    conn.commit()

def search_products(conn, query):
    """
    Search for products by product name or description.
    Relevance metric:
      - +2 points if the search query is found in the product name.
      - +1 point if found in the product description.
    """
    cursor = conn.cursor()
    # Lowercase the query for case-insensitive matching.
    query_lower = query.lower()
    like_query = f"%{query_lower}%"
    cursor.execute('''
        SELECT id, product_name, product_description,
        ((CASE WHEN lower(product_name) LIKE ? THEN 2 ELSE 0 END) +
         (CASE WHEN lower(product_description) LIKE ? THEN 1 ELSE 0 END)) as relevance
        FROM products
        WHERE lower(product_name) LIKE ? OR lower(product_description) LIKE ?
        ORDER BY relevance DESC, product_name ASC;
    ''', (like_query, like_query, like_query, like_query))
    return cursor.fetchall()

def main():
    conn = create_connection()
    create_tables(conn)
    insert_sample_data(conn)
    
    print("Welcome to the Product Search!")
    print("Type a search query to find products (or type 'exit' to quit).\n")
    
    while True:
        query = input("Enter your search query: ")
        if query.lower() == 'exit':
            break
        results = search_products(conn, query)
        if results:
            print("\nSearch results:")
            for row in results:
                print(f"ID: {row[0]} | Name: {row[1]} | Description: {row[2]} | Relevance: {row[3]}")
        else:
            print("No products found matching your query.")
        print()  # extra line for spacing
    
    conn.close()

if __name__ == '__main__':
    main()
