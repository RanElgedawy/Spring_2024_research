import unittest
import requests
from task9test import app, generate_unsubscribe_link

class TestNewsletterFunctionality(unittest.TestCase):
    
    def test_verify_user_identity(self):
        # Mock request data with user's email
        email = 'test@gmail.com'
        
        # Generate unique unsubscribe link for the user
        unsubscribe_link = generate_unsubscribe_link(email)
        
        # Make an HTTP GET request to the unsubscribe link
        response = requests.get(unsubscribe_link)
        
        # Assert that the response indicates successful verification of the user's identity
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unsubscribe Page', response.text)
        self.assertIn('Please provide a reason for unsubscribing:', response.text)
    
    def test_generate_unique_unsubscribe_link(self):
        # Generate unique unsubscribe links for two different users
        unsubscribe_link1 = generate_unsubscribe_link('test@gmail.com')
        unsubscribe_link2 = generate_unsubscribe_link('user2@example.com')
        
        # Assert that the generated unsubscribe links are unique for each user
        self.assertNotEqual(unsubscribe_link1, unsubscribe_link2)
    
    def test_page_for_describing_reason(self):
        # Make an HTTP GET request to the unsubscribe page
        unsubscribe_page_url = 'http://localhost:5000/unsubscribe'  # Adjust the URL as needed
        response = requests.get(unsubscribe_page_url)
        
        # Assert that the response contains the form for providing the reason
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unsubscribe Page', response.text)
        self.assertIn('Please provide a reason for unsubscribing:', response.text)
    
    def test_unsubscribe_all_functionality(self):
        # Make an HTTP POST request to trigger the functionality
        unsubscribe_all_url = 'http://localhost:5000/unsubscribe_all'  # Adjust the URL as needed
        response = requests.post(unsubscribe_all_url)
        
        # Assert that the response indicates successful unsubscribing of all users
        self.assertEqual(response.status_code, 200)
        self.assertIn('All users unsubscribed successfully.', response.json()['message'])

if __name__ == '__main__':
    unittest.main()
