import sqlite3

# Database initialization and connection
conn = sqlite3.connect(':memory:')  # Using in-memory DB for testing
cursor = conn.cursor()

# Create tables
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS products")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        stock INTEGER NOT NULL DEFAULT 0
    )
''')

# Insert test data
cursor.executemany(
    'INSERT INTO users (username, is_admin) VALUES (?, ?)',
    [('admin1', 1), ('user1', 0), ('admin2', 1)]
)

cursor.executemany(
    'INSERT INTO products (name, price, description, stock) VALUES (?, ?, ?, ?)',
    [
        ('Laptop', 999.99, 'High-performance laptop', 10),
        ('Phone', 699.99, 'Latest smartphone', 25)
    ]
)
conn.commit()

def check_admin(user_id):
    """Verify if user has admin privileges"""
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

def add_product(user_id):
    """Admin function to add new product"""
    if not check_admin(user_id):
        print("Permission denied: Admin access required")
        return

    name = input("Enter product name: ")
    price = float(input("Enter price: "))
    description = input("Enter description: ")
    stock = int(input("Enter stock quantity: "))

    cursor.execute(
        'INSERT INTO products (name, price, description, stock) VALUES (?, ?, ?, ?)',
        (name, price, description, stock)
    )
    conn.commit()
    print("Product added successfully!")

def update_product(user_id):
    """Admin function to update existing product"""
    if not check_admin(user_id):
        print("Permission denied: Admin access required")
        return

    product_id = int(input("Enter product ID to update: "))
    
    # Get current values
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if not product:
        print("Product not found")
        return

    # Get new values (keep current if not provided)
    new_name = input(f"New name ({product[1]}): ") or product[1]
    new_price = float(input(f"New price ({product[2]}): ") or product[2])
    new_desc = input(f"New description ({product[3]}): ") or product[3]
    new_stock = int(input(f"New stock ({product[4]}): ") or product[4])

    cursor.execute('''
        UPDATE products
        SET name = ?, price = ?, description = ?, stock = ?
        WHERE id = ?
    ''', (new_name, new_price, new_desc, new_stock, product_id))
    conn.commit()
    print("Product updated successfully!")

def delete_product(user_id):
    """Admin function to remove product"""
    if not check_admin(user_id):
        print("Permission denied: Admin access required")
        return

    product_id = int(input("Enter product ID to delete: "))
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    print("Product deleted successfully!" if cursor.rowcount > 0 else "Product not found")

def list_products():
    """List all products"""
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    print("\nCurrent Products:")
    for p in products:
        print(f"{p[0]}: {p[1]} - ${p[2]} ({p[4]} in stock)")

def test_interface():
    """Command-line interface for testing"""
    while True:
        try:
            user_id = int(input("\nEnter your user ID (0 to exit): "))
        except ValueError:
            print("Please enter a valid number")
            continue
            
        if user_id == 0:
            break
            
        # Verify user exists
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            print("User not found")
            continue

        while True:
            print("\nActions:")
            print("1. List products")
            print("2. Add product")
            print("3. Update product")
            print("4. Delete product")
            print("5. Switch user")
            action = input("Choose action: ")

            if action == '1':
                list_products()
            elif action == '2':
                add_product(user_id)
            elif action == '3':
                update_product(user_id)
            elif action == '4':
                delete_product(user_id)
            elif action == '5':
                break
            else:
                print("Invalid choice")

    conn.close()
    print("Exiting...")

if __name__ == '__main__':
    print("=== E-commerce Admin Test Interface ===")
    print("Test users: (1: admin1), (2: user1), (3: admin2)")
    test_interface()