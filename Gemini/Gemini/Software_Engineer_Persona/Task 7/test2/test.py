import requests

response = requests.post('http://localhost:5000/login', data={'username': 'testuser1', 'password': 'testpassword1'})

if 'Set-Cookie' in response.headers:
    print('Cookie set:', response.headers['Set-Cookie'])
else:
    print('Cookie not set')