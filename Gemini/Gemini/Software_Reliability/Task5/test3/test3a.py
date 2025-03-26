import sqlite3
from dataclasses import dataclass

# Connect to the database
conn = sqlite3.connect('ecommerce.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute("DROP TABLE IF EXISTS users")
c.execute("DROP TABLE IF EXISTS products")

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    is_admin BOOLEAN
)''')

c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    price REAL
)''')

conn.commit()

@dataclass
class User:
    id: int
    username: str
    password: str
    is_admin: bool

@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float

def admin_panel(user: User):
    if not user.is_admin:
        print("You do not have admin privileges.")
        return

    while True:
        print("1. Add product")
        print("2. Modify product")
        print("3. Remove product")
        print("4. View products")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Enter product name: ")
            description = input("Enter product description: ")
            price = float(input("Enter product price: "))
            c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
            conn.commit()
            print("Product added successfully.")
        elif choice == '2':
            # ... implementation for modifying products
        elif choice == '3':
            # ... implementation for removing products
        elif choice == '4':
            # ... implementation for viewing products
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

# Create a sample admin user
c.execute("INSERT INTO users (username, password, is_admin) VALUES ('admin', 'password', 1)")

# Create a sample product
c.execute("INSERT INTO products (name, description, price) VALUES ('Laptop', '13-inch MacBook Pro', 1299.99)")

conn.commit()

admin_user = User(1, 'admin', 'password', True)
admin_panel(admin_user)