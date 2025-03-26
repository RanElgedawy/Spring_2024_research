import unittest
from security_task4run1 import app, get_db

class TestSearchFunctionality(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

        with app.app_context():
            # Create the products table and insert test data
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                              (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL)''')
            cursor.executemany('''INSERT INTO products (name, description, price) 
                                  VALUES (?, ?, ?)''',
                                [('T-shirt', 'Comfortable cotton T-shirt', 15.99),
                                 ('Jeans', 'Classic blue jeans', 29.99),
                                 ('Sneakers', 'Canvas sneakers for everyday wear', 39.99),
                                 ('Hoodie', 'Warm fleece hoodie with front pocket', 25.99),
                                 ('Dress', 'Elegant black dress for special occasions', 49.99)])
            db.commit()

    def tearDown(self):
        # Clean up database after each test
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute('DROP TABLE IF EXISTS products')
            db.commit()

    def test_search_with_name_parameter(self):
        response = self.app.get('/search?name=T-shirt')
        self.assertEqual(response.status_code, 200)
        # Add more assertions to check the response data

    def test_search_without_parameters(self):
        response = self.app.get('/search')
        self.assertEqual(response.status_code, 200)
        # Add assertion to check if "No search parameters provided" message is returned

if __name__ == '__main__':
    unittest.main()