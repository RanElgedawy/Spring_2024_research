import sqlite3
from contextlib import closing

# Database setup
def init_db():
    with sqlite3.connect('ecommerce.db') as conn:
        with closing(conn.cursor()) as c:
            c.execute("DROP TABLE IF EXISTS users")
            c.execute("DROP TABLE IF EXISTS products")

            # Create users table
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password_hash TEXT,
                        is_admin BOOLEAN)''')

            # Create products table
            c.execute('''CREATE TABLE IF NOT EXISTS products
                        (id INTEGER PRIMARY KEY,
                        name TEXT,
                        price REAL,
                        description TEXT,
                        stock INTEGER)''')
            
            # Insert test data
            c.execute("INSERT OR IGNORE INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                     ('admin@example.com', 'hashed_password', 1))
            c.execute("INSERT OR IGNORE INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                     ('user@example.com', 'hashed_password', 0))
            
            # Insert sample product
            c.execute("INSERT OR IGNORE INTO products (name, price, description, stock) VALUES (?, ?, ?, ?)",
                     ('Laptop', 999.99, 'High-performance laptop', 10))
            
        conn.commit()

# Current user simulation (replace with your actual authentication mechanism)
current_user_id = 1  # Change this to test different users

def check_admin():
    """Verify if current user has admin privileges"""
    with sqlite3.connect('ecommerce.db') as conn:
        with closing(conn.cursor()) as c:
            c.execute("SELECT is_admin FROM users WHERE id = ?", (current_user_id,))
            result = c.fetchone()
            return result and result[0] == 1

# Product management functions
def add_product(name, price, description, stock):
    if not check_admin():
        raise PermissionError("Admin privileges required")
    
    with sqlite3.connect('ecommerce.db') as conn:
        with closing(conn.cursor()) as c:
            c.execute("INSERT INTO products (name, price, description, stock) VALUES (?, ?, ?, ?)",
                     (name, price, description, stock))
        conn.commit()

def update_product(product_id, **kwargs):
    if not check_admin():
        raise PermissionError("Admin privileges required")
    
    valid_fields = {'name', 'price', 'description', 'stock'}
    updates = {k: v for k, v in kwargs.items() if k in valid_fields}
    
    if not updates:
        raise ValueError("No valid fields to update")
    
    set_clause = ', '.join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [product_id]
    
    with sqlite3.connect('ecommerce.db') as conn:
        with closing(conn.cursor()) as c:
            c.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)
            if c.rowcount == 0:
                raise ValueError("Product not found")
        conn.commit()

def delete_product(product_id):
    if not check_admin():
        raise PermissionError("Admin privileges required")
    
    with sqlite3.connect('ecommerce.db') as conn:
        with closing(conn.cursor()) as c:
            c.execute("DELETE FROM products WHERE id = ?", (product_id,))
            if c.rowcount == 0:
                raise ValueError("Product not found")
        conn.commit()

def get_products():
    with sqlite3.connect('ecommerce.db') as conn:
        with closing(conn.cursor()) as c:
            c.execute("SELECT * FROM products")
            return c.fetchall()

# Test function
def test_admin_functions():
    global current_user_id
    
    print("Initial products:", get_products())
    
    # Test as admin
    current_user_id = 1
    try:
        add_product("Smartphone", 699.99, "Latest model smartphone", 25)
        print("Product added successfully")
        
        update_product(2, price=649.99, stock=20)
        print("Product updated successfully")
        
        delete_product(2)
        print("Product deleted successfully")
        
    except Exception as e:
        print("Admin test error:", e)
    
    # Test as regular user
    current_user_id = 2
    try:
        add_product("Unauthorized Product", 99.99, "Should not be added", 5)
    except PermissionError as e:
        print("Regular user test passed (caught permission error):", e)
    
    print("Final products:", get_products())

if __name__ == '__main__':
    init_db()
    test_admin_functions()