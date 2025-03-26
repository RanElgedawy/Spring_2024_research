import sqlite3

# Create an in-memory SQLite database (or change ":memory:" to a filename for a persistent DB)
conn = sqlite3.connect(":memory:")
conn.enable_load_extension(True)
# Enable FTS5 extension if not already built in (modern SQLite builds already include FTS5)
try:
    conn.execute("SELECT fts5('simple')")
except sqlite3.OperationalError:
    conn.load_extension("fts5")

cursor = conn.cursor()

# Create a standard products table
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
''')

# Create an FTS5 virtual table to index products for full-text search.
# It is linked to the products table so that we can update both.
cursor.execute('''
    CREATE VIRTUAL TABLE products_fts USING fts5(
        name, 
        description, 
        content='products', 
        content_rowid='id'
    )
''')

# Function to insert a product into both tables
def add_product(name, description):
    cursor.execute("INSERT INTO products (name, description) VALUES (?, ?)", (name, description))
    # Get the rowid of the inserted product
    rowid = cursor.lastrowid
    # Insert into the FTS table. The "content" option keeps this in sync automatically if using triggers.
    cursor.execute("INSERT INTO products_fts(rowid, name, description) VALUES (?, ?, ?)",
                   (rowid, name, description))
    conn.commit()

# Insert some test products
test_products = [
    ("Apple iPhone 14", "Latest Apple smartphone with A15 chip and improved battery life."),
    ("Samsung Galaxy S22", "Flagship phone with high-resolution camera and sleek design."),
    ("Dell XPS 13", "Lightweight laptop with high performance and long battery life."),
    ("Sony WH-1000XM4", "Noise cancelling over-ear headphones with excellent sound quality."),
    ("Apple MacBook Pro", "Powerful laptop with M1 chip designed for professionals.")
]

for name, description in test_products:
    add_product(name, description)

# Function to search products using FTS
def search_products(query, limit=5):
    """
    Search for products matching the query in name and description.
    Returns the top results ranked by relevance (using the bm25 ranking function).
    """
    # Use bm25 ranking to order the results.
    sql = '''
    SELECT p.id, p.name, p.description,
           bm25(products_fts) as score
      FROM products_fts JOIN products p ON (products_fts.rowid = p.id)
     WHERE products_fts MATCH ?
     ORDER BY score
     LIMIT ?
    '''
    cursor.execute(sql, (query, limit))
    return cursor.fetchall()

# Test the search functionality interactively
def main():
    print("Product Search Test")
    print("===================")
    while True:
        query = input("Enter search term (or 'exit' to quit): ")
        if query.lower() == "exit":
            break
        results = search_products(query)
        if results:
            print("\nSearch results:")
            for prod in results:
                print(f"ID: {prod[0]}, Name: {prod[1]}, Description: {prod[2]}, Score: {prod[3]:.2f}")
        else:
            print("No products found matching your query.")
        print("\n-------------------\n")

if __name__ == '__main__':
    main()
