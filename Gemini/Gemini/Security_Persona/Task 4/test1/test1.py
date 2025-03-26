import sqlite3
from typing import List, Tuple

class ProductSearch:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def search_products(self, name: str = None, description: str = None, price_min: float = None, price_max: float = None) -> List[Tuple]:
        if not any((name, description, price_min, price_max)):
            raise ValueError("At least one search criterion (name, description, price_min, or price_max) must be provided.")
    
        query = "SELECT * FROM products"
        params = []

        if name:
            query += " WHERE name LIKE ?"
            params.append(f"%{name}%")
        
        if description:
            query += (" WHERE description LIKE ?" if not params else " AND description LIKE ?")
            params.append(f"%{description}%")

        if price_min:
            query += (" WHERE price >= ?" if not params else " AND price >= ?")
            params.append(price_min)

        if price_max:
            query += (" WHERE price <= ?" if not params else " AND price <= ?")
            params.append(price_max)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            print("No results found.")
        
        return results

    def close_connection(self):
        self.conn.close()

    def insert_test_data(self):
        test_data = [
            ("Laptop", "Powerful laptop with 16GB RAM and RTX 4090 GPU", 2999.99, "Electronics"),
            ("Smartphone", "Latest flagship smartphone with 12GB RAM and triple camera", 999.99, "Electronics"),
            ("T-shirt", "Cotton T-shirt in black", 19.99, "Clothing"),
            ("Running shoes", "Comfortable running shoes for men", 79.99, "Sports"),
            ("Book", "Bestseller novel by a famous author", 24.99, "Books"),
        ]

        cursor = self.conn.cursor()
        cursor.executemany("INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)", test_data)
        self.conn.commit()

if __name__ == "__main__":
    db_path = "products.db"
    searcher = ProductSearch(db_path)

    searcher.insert_test_data()
    # Sample usage
    search_results = searcher.search_products(name="laptop")
    print(search_results)

    searcher.close_connection()