import requests

# Set the base URL of the Flask application
base_url = 'http://localhost:5000'

# Dummy token for authentication
headers = {'Authorization': 'Bearer dummy_token'}

# Example data for testing
cart_data = {
    "user_id": 100,
    "cart_items": [
        {"product_id": 1, "quantity": 2, "price": 10},
        {"product_id": 2, "quantity": 1, "price": 20}
    ]
}

# Endpoint URL for checkout
checkout_url = f'{base_url}/checkout'

# Send a POST request to checkout endpoint
response = requests.post(checkout_url, headers=headers, json=cart_data)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    try:
        # Print the response content
        print(response.json())
    except ValueError:
        # If the response content is not in JSON format, print it as text
        print(response.text)
else:
    # If the request was not successful, print the status code and reason
    print(f"Request failed with status code {response.status_code}: {response.reason}")
