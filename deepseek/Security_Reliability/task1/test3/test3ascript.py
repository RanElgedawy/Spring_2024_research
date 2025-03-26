import requests

BASE_URL = 'http://127.0.0.1:5000'

def test_register(username, password):
    response = requests.post(f'{BASE_URL}/register', json={'username': username, 'password': password})
    print(response.json())

def test_login(username, password):
    response = requests.post(f'{BASE_URL}/login', json={'username': username, 'password': password})
    print(response.json())

if __name__ == '__main__':
    # Test registration
    test_register('testuser', 'securepassword123')

    # Test login with correct credentials
    test_login('testuser', 'securepassword123')

    # Test login with incorrect credentials
    test_login('testuser', 'wrongpassword')