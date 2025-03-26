import pytest
import requests

@pytest.fixture
def base_url():
    return 'http://localhost:5000'

@pytest.fixture
def user_id():
    return 1  # Assuming user_id for testing purposes

def test_register_card(base_url, user_id):
    # Mock data for card registration
    card_data = {
        'user_id': user_id,
        'card_number': '1234567890123456',
        'cvv': '123',
        'expiration_date': '12/2025',  # Valid expiration date
        'name_on_card': 'John Doe',
        'billing_zip': '12345'
    }

    # Send a POST request to register a card
    response = requests.post(f'{base_url}/register_card', json=card_data)

    # Assert the status code is 200
    assert response.status_code == 200

    # Assert the response message indicates successful registration
    assert response.json()['message'] == 'Payment card registered successfully'

if __name__ == '__main__':
    pytest.main(['-s', __file__])
