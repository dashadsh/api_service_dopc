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

# ===================== Unit tests =====================

def test_zero_distance_calculation():
	assert calculate_distance(60.0, 24.0, 60.0, 24.0) == 0

def test_calculation_formula(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=800&user_lat=60.18094&user_lon=24.93087')
	data = response.get_json()
	assert data['small_order_surcharge'] == 200
	assert data['cart_value'] == 800
	assert data['total_price'] == data['cart_value'] + data['small_order_surcharge'] + data['delivery']['fee']

def test_delivery_ranges(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=61.0&user_lon=24.93')
	assert response.status_code == 400
	assert response.get_json()['error']['code'] == 'ERR_NO_DELIVERY'

# ===================== Negative tests =====================

def test_maximum_coordinates(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=91&user_lon=181')
	assert response.status_code == 400

def test_minimum_coordinates(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=-91&user_lon=-181')
	assert response.status_code == 400

def test_missing_key(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&user_lat=-90&user_lon=180')
	assert response.status_code == 400

def test_missing_value(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=-90&user_lon=')
	assert response.status_code == 400

class TestMalformedQuery:
	@pytest.mark.parametrize("test_case", [
		{
			"slug": "home-assignment-venue-helsinki",
			"cart": "not_a_number",
			"lat": "60.18094",
			"lon": "24.93087"},
		{
			"slug": "home-assignment-venue-helsinki",
			"cart": "1000",
			"lat": "60.18094",
			"lon": "!$%^&*()"},
		])

	def test_invalid_params(self, client, test_case):
		response = client.get(f'/api/v1/delivery-order-price?venue_slug={test_case["slug"]}&cart_value={test_case["cart"]}&user_lat={test_case["lat"]}&user_lon={test_case["lon"]}')
		assert response.status_code == 400

class TestMalformedVenues:
	@pytest.mark.parametrize("venue_data", [
		{
			"slug": "home-assignment-venue-helsink",
			"cart": 1000,
			"lat": 60.18094,
			"lon": 24.93087},
		# Identical to:
		# curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=%^&*()&cart_value=1000&user_lat=60.18094&user_lon=24.93087"
		{
			"slug": "%25%5E%26*()",
			"cart": 1000,
			"lat": 60.18094,
			"lon": 24.93087},
		])
	
	def test_invalid_venues(self, client, venue_data):
		response = client.get(f'/api/v1/delivery-order-price?venue_slug={venue_data["slug"]}&cart_value={venue_data["cart"]}&user_lat={venue_data["lat"]}&user_lon={venue_data["lon"]}')
		assert response.status_code == 404

def test_delivery_too_far(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=61.18094&user_lon=24.93087')
	assert response.status_code == 400
	data = response.get_json()
	assert "distance" in data['error']['errors'][0]['field']

# ===================== Positive tests =====================

def test_large_cart_value(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=9999999999&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 200

def test_zero_cart_value(client):
	response = client.get('/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=0&user_lat=60.18094&user_lon=24.93087')
	assert response.status_code == 200

class TestValidRequests:
    @pytest.mark.parametrize("venue_data", [
        {
            "slug": "home-assignment-venue-helsinki",
            "lat": 60.18094,
            "lon": 24.93087,
            "cart": 1000
        },
        {
            "slug": "home-assignment-venue-stockholm",
            "lat": 59.35683,
            "lon": 18.03150,
            "cart": 10000
        },
        {
            "slug": "home-assignment-venue-berlin",
            "lat": 52.51032,
            "lon": 13.45361,
            "cart": 1000
        },
        {
            "slug": "home-assignment-venue-tokyo",
            "lat": 35.65591,
            "lon": 139.71153,
            "cart": 700
        }
    ])
    def test_valid_requests(self, client, venue_data):
        response = client.get(f'/api/v1/delivery-order-price?venue_slug={venue_data["slug"]}&cart_value={venue_data["cart"]}&user_lat={venue_data["lat"]}&user_lon={venue_data["lon"]}')
        assert response.status_code == 200
        data = response.get_json()
        assert all(key in data for key in ['total_price', 'small_order_surcharge', 'cart_value', 'delivery'])
        assert all(isinstance(data['delivery'][key], int) for key in ['distance', 'fee'])