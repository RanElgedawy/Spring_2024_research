#!/usr/bin/env python3
import argparse
import sqlite3
import sys

DB_NAME = "ecommerce.db"

def init_db():
    """Create the users and products tables and seed test data."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Create users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        is_admin INTEGER
    )
    """)
    
    # Create products table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        description TEXT
    )
    """)
    
    # Seed test data if tables are empty
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        users = [
            ("admin", 1),    # admin user
            ("user1", 0)     # non-admin user
        ]
        cur.executemany("INSERT INTO users (username, is_admin) VALUES (?, ?)", users)
        print("Seeded users table with admin and regular user.")
    
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ("Widget", 19.99, "A useful widget"),
            ("Gadget", 29.99, "A fancy gadget")
        ]
        cur.executemany("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", products)
        print("Seeded products table with sample products.")
    
    conn.commit()
    return conn

def is_admin(conn, username):
    """Check if a given username has admin privileges."""
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    return bool(row and row[0] == 1)

def add_product(conn, name, price, description):
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", (name, price, description))
    conn.commit()
    print(f"Added product '{name}' with price {price} and description '{description}'.")

def update_product(conn, product_id, name, price, description):
    cur = conn.cursor()
    cur.execute("UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?", (name, price, description, product_id))
    if cur.rowcount == 0:
        print(f"No product found with id {product_id}.")
    else:
        conn.commit()
        print(f"Updated product id {product_id} to '{name}', price {price}, description '{description}'.")

def delete_product(conn, product_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cur.rowcount == 0:
        print(f"No product found with id {product_id}.")
    else:
        conn.commit()
        print(f"Deleted product with id {product_id}.")

def list_products(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, description FROM products")
    rows = cur.fetchall()
    if not rows:
        print("No products available.")
    else:
        print("Current Products:")
        for row in rows:
            print(f"ID: {row[0]} | Name: {row[1]} | Price: {row[2]} | Description: {row[3]}")

def main():
    parser = argparse.ArgumentParser(description="Admin tool to manage products.")
    parser.add_argument("--username", required=True, help="The username of the logged-in user")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # Add product command
    parser_add = subparsers.add_parser("add", help="Add a new product")
    parser_add.add_argument("name", help="Name of the product")
    parser_add.add_argument("price", type=float, help="Price of the product")
    parser_add.add_argument("description", help="Description of the product")

    # Update product command
    parser_update = subparsers.add_parser("update", help="Update an existing product")
    parser_update.add_argument("id", type=int, help="ID of the product to update")
    parser_update.add_argument("name", help="New name for the product")
    parser_update.add_argument("price", type=float, help="New price for the product")
    parser_update.add_argument("description", help="New description for the product")

    # Delete product command
    parser_delete = subparsers.add_parser("delete", help="Delete a product")
    parser_delete.add_argument("id", type=int, help="ID of the product to delete")

    # List products command
    parser_list = subparsers.add_parser("list", help="List all products")

    args = parser.parse_args()

    conn = init_db()

    # Verify admin privileges
    if not is_admin(conn, args.username):
        print("Error: You do not have admin privileges to perform this action.")
        sys.exit(1)

    # Execute the chosen command
    if args.command == "add":
        add_product(conn, args.name, args.price, args.description)
    elif args.command == "update":
        update_product(conn, args.id, args.name, args.price, args.description)
    elif args.command == "delete":
        delete_product(conn, args.id)
    elif args.command == "list":
        list_products(conn)
    else:
        print("Unknown command.")
    
    conn.close()

if __name__ == "__main__":
    main()
