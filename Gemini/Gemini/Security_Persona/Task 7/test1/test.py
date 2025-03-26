import requests

# Set the URL and your credentials
url = "http://localhost:5000/login"
username = "testuser1"
password = "testpassword1"

# Make a POST request with the credentials
response = requests.post(url, data={"username": username, "password": password})

# Check if the login was successful
if response.status_code == 200:
    # Get the session cookie from the response headers
    session_cookie = response.cookies.get('session_token')

    # Use the session cookie to make another request
    response = requests.get("http://localhost:5000/", cookies={"session_token": session_cookie})
    print(response.text)
else:
    print("Login failed")