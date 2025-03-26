from security_task4run2 import app, db
from security_task4run2 import Product
import random

# Generate some test data
def generate_test_data():
    products = []
    for i in range(10):
        product = Product(
            name=f'Product {i}',
            description=f'Description of Product {i}',
            price=random.uniform(10, 100)  # Random price between 10 and 100
        )
        products.append(product)
    return products

# Insert test data into the database
def insert_test_data():
    with app.app_context():
        test_products = generate_test_data()
        for product in test_products:
            db.session.add(product)
        db.session.commit()

if __name__ == '__main__':
    insert_test_data()