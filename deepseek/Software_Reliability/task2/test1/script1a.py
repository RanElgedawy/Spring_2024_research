import requests

# Test product retrieval
print("Testing product retrieval:")
response = requests.get('http://localhost:5000/products/1')
print(f"GET /products/1: {response.status_code} {response.json()}")

# Test cart functionality
headers = {'X-User-ID': '1'}
print("\nTesting cart additions:")

# First addition (5 items)
response = requests.post(
    'http://localhost:5000/cart/add',
    json={'product_id': 1, 'quantity': 5},
    headers=headers
)
print(f"POST /cart/add (5 items): {response.status_code} {response.json()}")

# Try to exceed stock (6 more items)
response = requests.post(
    'http://localhost:5000/cart/add',
    json={'product_id': 1, 'quantity': 6},
    headers=headers
)
print(f"POST /cart/add (6 items): {response.status_code} {response.json()}")

# Add remaining stock (5 more items)
response = requests.post(
    'http://localhost:5000/cart/add',
    json={'product_id': 1, 'quantity': 5},
    headers=headers
)
print(f"POST /cart/add (5 items): {response.status_code} {response.json()}")