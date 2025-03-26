import sqlite3
from sqlite3 import Error
from datetime import datetime

def create_tables(conn):
    """Create database tables"""
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS products")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")

def insert_sample_data(conn):
    """Insert test data into database"""
    products = [
        ('Blue Shirt', 'A comfortable cotton shirt in blue', 29.99, '2023-01-15'),
        ('Red T-Shirt', 'Red cotton t-shirt with logo', 24.99, '2023-02-01'),
        ('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 49.99, '2023-03-10'),
        ('Coffee Mug', 'Ceramic mug with "Best Developer" text', 12.50, '2023-04-05'),
        ('Test Product; DROP TABLE users;--', 'SQL injection test product', 999.99, '2023-05-01')
    ]
    
    try:
        cur = conn.cursor()
        cur.executemany("""
            INSERT INTO products (name, description, price, created_at)
            VALUES (?, ?, ?, ?)
        """, products)
        conn.commit()
    except Error as e:
        print(f"Error inserting sample data: {e}")

def search_products(conn, search_query=None, min_price=None, max_price=None):
    """
    Search products with relevance scoring
    Relevance based on: number of search terms matched in name/description
    """
    try:
        cur = conn.cursor()
        terms = search_query.split() if search_query else []
        params = []
        relevance_parts = []
        conditions = []

        # Build search relevance and conditions
        for term in terms:
            term_param = f"%{term}%"
            relevance_parts.append(
                "(CASE WHEN (name LIKE ? OR description LIKE ?) THEN 1 ELSE 0 END)"
            )
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([term_param, term_param])

        # Build price conditions
        price_conditions = []
        if min_price is not None:
            price_conditions.append("price >= ?")
            params.append(min_price)
        if max_price is not None:
            price_conditions.append("price <= ?")
            params.append(max_price)

        # Construct full query
        relevance_expr = " + ".join(relevance_parts) if relevance_parts else "0"
        where_clause = []
        
        if conditions:
            where_clause.append(f"({' OR '.join(conditions)})")
        if price_conditions:
            where_clause.append(f"({' AND '.join(price_conditions)})")
            
        where_str = " AND ".join(where_clause) if where_clause else "1=1"

        query = f"""
            SELECT *, ({relevance_expr}) AS relevance
            FROM products
            WHERE {where_str}
            ORDER BY relevance DESC, created_at DESC
        """

        cur.execute(query, params)
        results = cur.fetchall()
        
        # Return results with column names
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in results]
        
    except Error as e:
        print(f"Search error: {e}")
        return []

def test_search_functionality():
    """Test the search functionality with different scenarios"""
    # Create in-memory database for testing
    conn = sqlite3.connect(':memory:')
    create_tables(conn)
    insert_sample_data(conn)
    
    test_cases = [
        ("Basic search", {"search_query": "blue shirt"}),
        ("Price filter", {"min_price": 20, "max_price": 30}),
        ("Combined search", {"search_query": "cotton", "min_price": 15, "max_price": 30}),
        ("SQL injection attempt", {"search_query": "'; DROP TABLE products--"}),
        ("No results", {"search_query": "nonexistent product", "min_price": 1000}),
        ("Empty search", {})
    ]
    
    for name, params in test_cases:
        print(f"\nTest Case: {name}")
        print(f"Parameters: {params}")
        results = search_products(conn, **params)
        
        if not results:
            print("No results found")
            continue
            
        for product in results:
            print(f"[Relevance: {product['relevance']}] {product['name']} - ${product['price']:.2f}")
            print(f"Description: {product['description']}\n")
    
    conn.close()

if __name__ == "__main__":
    test_search_functionality()