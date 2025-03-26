import requests

BASE_URL = 'http://127.0.0.1:5000'

# Test getting a product
product_id = 1
response = requests.get(f'{BASE_URL}/products/{product_id}')
print(f"Get Product {product_id}: Status Code - {response.status_code}")
print(f"Get Product {product_id}: JSON - {response.json()}")

# Test adding a product to cart (assuming user_id=1 exists)
add_to_cart_data = {
    'user_id': 1,
    'product_id': 2,
    'quantity': 2
}
response = requests.post(f'{BASE_URL}/cart', data=add_to_cart_data)
print(f"\nAdd to Cart: Status Code - {response.status_code}")
print(f"Add to Cart: JSON - {response.json()}")

# Test adding the same product again to increase quantity
add_to_cart_data_again = {
    'user_id': 1,
    'product_id': 2,
    'quantity': 1
}
response = requests.post(f'{BASE_URL}/cart', data=add_to_cart_data_again)
print(f"\nAdd to Cart Again: Status Code - {response.status_code}")
print(f"Add to Cart Again: JSON - {response.json()}")

# Test adding a product with insufficient stock
add_insufficient_stock = {
    'user_id': 1,
    'product_id': 1,
    'quantity': 15
}
response = requests.post(f'{BASE_URL}/cart', data=add_insufficient_stock)
print(f"\nAdd Insufficient Stock: Status Code - {response.status_code}")
print(f"Add Insufficient Stock: JSON - {response.json()}")

# Test adding a product that doesn't exist
add_non_existent_product = {
    'user_id': 1,
    'product_id': 999,
    'quantity': 1
}
response = requests.post(f'{BASE_URL}/cart', data=add_non_existent_product)
print(f"\nAdd Non-Existent Product: Status Code - {response.status_code}")
print(f"Add Non-Existent Product: JSON - {response.json()}")