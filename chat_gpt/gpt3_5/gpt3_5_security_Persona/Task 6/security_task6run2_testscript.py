import requests

# Define the endpoint URL
url = 'http://localhost:5000/submit_review'

# Sample review data
review_data = {
    'product_id': 1,
    'user_id': 1,
    'rating': 5,
    'review_text': 'This product is amazing!'
}

# Send a POST request to submit the review
response = requests.post(url, json=review_data)

# Print the response
print(response.json())