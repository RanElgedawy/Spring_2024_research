import requests

BASE_URL = 'https://localhost:5000'

# Disable SSL verification warning for testing
requests.packages.urllib3.disable_warnings()

session = requests.Session()
session.verify = False  # Only for testing!

# Test protected route without login
response = session.get(BASE_URL)
print(f'Access without login: {response.status_code}')  # Should redirect

# Test login
login_data = {'username': 'test', 'password': 'testpass'}
response = session.post(f'{BASE_URL}/login', data=login_data)
print(f'Login status: {response.status_code}')  # Should be 200

# Test access after login
response = session.get(BASE_URL)
print(f'Access after login: {response.status_code}')  # Should be 200

# Test logout
response = session.get(f'{BASE_URL}/logout')
print(f'Logout status: {response.status_code}')  # Should redirect

# Test access after logout
response = session.get(BASE_URL)
print(f'Access after logout: {response.status_code}')  # Should redirect