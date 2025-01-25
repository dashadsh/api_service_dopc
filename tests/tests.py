# tests/tests.py
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dopc.app import app, calculate_distance

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_error_response_format(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=invalid&cart_value=1000&user_lat=60.18094&user_lon=24.93087')
	data = response.get_json()
	assert response.status_code == 404
	assert 'status_code' in data
	assert 'error' in data
	assert 'code' in data['error']
	assert 'message' in data['error']
	assert 'errors' in data['error']

def test_zero_distance_calculation():
	assert calculate_distance(60.0, 24.0, 60.0, 24.0) == 0

def test_helsinki_pricing(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=800&user_lat=60.18094&user_lon=24.93087')
	data = response.get_json()
	assert data['small_order_surcharge'] == 200
	assert data['cart_value'] == 800
	assert data['total_price'] == data['cart_value'] + data['small_order_surcharge'] + data['delivery']['fee']

def test_stockholm_large_order(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-stockholm&cart_value=15000&user_lat=59.35683&user_lon=18.03150')
	data = response.get_json()
	assert data['small_order_surcharge'] == 0

def test_berlin_minimum_order(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-berlin&cart_value=1000&user_lat=52.51032&user_lon=13.45361')
	data = response.get_json()
	assert data['small_order_surcharge'] == 0

def test_delivery_ranges(client):
	# Test max range
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=61.0&user_lon=24.93')
	assert response.status_code == 400
	assert response.get_json()['error']['code'] == 'ERR_NO_DELIVERY'

def test_maximum_coordinates(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=90&user_lon=180')
	assert response.status_code == 400

def test_minimum_coordinates(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=-90&user_lon=-180')
	assert response.status_code == 400

def test_zero_cart_value(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=0&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 200

def test_malformed_cart_value(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=not_a_number&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 400

def test_malformed_coordinates(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=60.18094&user_lon=!$%^&*()')
	assert response.status_code == 400

def test_malformed_venue_slug(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsink&cart_value=1000&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 404

# test: curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=%^&*()&cart_value=1000&user_lat=60.18094&user_lon=24.93087"
def test_special_characters_venue_error_format(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=%25%5E%26*()&cart_value=1000&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 404

def test_delivery_too_far(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=61.18094&user_lon=24.93087')
	assert response.status_code == 400
	data = response.get_json()
	assert "distance" in data['error']['errors'][0]['field']

def test_valid_helsinki_request(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 200
	# .json() is from the requests library (for making HTTP requests)
	# .get_json() is from Flask's test client (for testing Flask apps)
	data = response.get_json()
	assert 'total_price' in data
	assert 'small_order_surcharge' in data
	assert 'cart_value' in data
	assert 'delivery' in data
	assert isinstance(data['delivery']['distance'], int)
	assert isinstance(data['delivery']['fee'], int)

def test_valid_stockholm_request(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-stockholm&cart_value=10000&user_lat=59.35683&user_lon=18.03150')
	assert response.status_code == 200
	data = response.get_json()
	assert 'total_price' in data
	assert 'small_order_surcharge' in data
	assert 'cart_value' in data
	assert 'delivery' in data
	assert isinstance(data['delivery']['distance'], int)
	assert isinstance(data['delivery']['fee'], int)

def test_valid_berlin_request(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-berlin&cart_value=1000&user_lat=52.51032&user_lon=13.45361')
	assert response.status_code == 200
	data = response.get_json()
	assert 'total_price' in data
	assert 'small_order_surcharge' in data
	assert 'cart_value' in data
	assert 'delivery' in data
	assert isinstance(data['delivery']['distance'], int)
	assert isinstance(data['delivery']['fee'], int)

def test_valid_tokyo_request(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-tokyo&cart_value=700&user_lat=35.65591&user_lon=139.71153')
	assert response.status_code == 200
	data = response.get_json()
	assert 'total_price' in data
	assert 'small_order_surcharge' in data
	assert 'cart_value' in data
	assert 'delivery' in data
	assert isinstance(data['delivery']['distance'], int)
	assert isinstance(data['delivery']['fee'], int)
