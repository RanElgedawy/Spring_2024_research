from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import sqlite3
from fastapi.testclient import TestClient

app = FastAPI()

# Database connection setup
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if they don't exist
def create_tables():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        db.commit()

create_tables()

# Pydantic models for API requests/responses
class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int

class AddToCart(BaseModel):
    user_id: int
    product_id: int
    quantity: int

# Helper function to get product by id
def get_product_by_id(product_id: int):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product)

# API to retrieve product information
@app.get("/product/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = get_product_by_id(product_id)
    return Product(**product)

# API to add products to a user's cart
@app.post("/cart/add")
def add_to_cart(cart_item: AddToCart):
    db = get_db()

    # Check if the product exists and has enough stock
    product = get_product_by_id(cart_item.product_id)
    if product["stock"] < cart_item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    # Add product to user's cart
    db.execute('''
        INSERT INTO carts (user_id, product_id, quantity)
        VALUES (?, ?, ?)
    ''', (cart_item.user_id, cart_item.product_id, cart_item.quantity))

    # Decrease the product stock in the product table
    new_stock = product["stock"] - cart_item.quantity
    db.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, cart_item.product_id))
    db.commit()

    return {"message": "Product added to cart successfully"}

# Test client to test API functionality
client = TestClient(app)

# Populate some initial data for testing
def seed_data():
    db = get_db()

    # Seed users
    db.execute("INSERT OR IGNORE INTO users (username) VALUES ('user1')")
    db.execute("INSERT OR IGNORE INTO users (username) VALUES ('user2')")

    # Seed products
    db.execute("INSERT OR IGNORE INTO products (name, price, stock) VALUES ('Product A', 10.99, 100)")
    db.execute("INSERT OR IGNORE INTO products (name, price, stock) VALUES ('Product B', 15.99, 50)")
    db.commit()

seed_data()

# Test function to ensure everything works
def test_api():
    # Test retrieving a product
    response = client.get("/product/1")
    assert response.status_code == 200
    print(response.json())

    # Test adding product to the cart
    add_cart_response = client.post("/cart/add", json={"user_id": 1, "product_id": 1, "quantity": 2})
    assert add_cart_response.status_code == 200
    print(add_cart_response.json())

    # Test that stock was reduced
    response_after = client.get("/product/1")
    print(response_after.json())

if __name__ == "__main__":
    test_api()