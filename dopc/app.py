# dopc/app.py
from flask import Flask, request, jsonify
import requests
from typing import List, Dict, Optional
from haversine import haversine, Unit

app = Flask(__name__)

BASE_URL = "https://consumer-api.development.dev.woltapi.com/home-assignment-api/v1/venues"

ERR_REQUEST = "ERR_INVALID_REQUEST_PARAMS"
ERR_NO_DELIVERY = "ERR_NO_DELIVERY"
ERR_API = "ERR_EXTERNAL_API_FAILURE"
ERR_SERVER = "ERR_SERVER"

def make_error(status_code: int, code: str, message: str, errors: List[Dict[str, str]] = None):
	"""
	Generates a JSON error response with given parameters.
	Returns:
		Tuple[Dict, int]: JSON response, HTTP status code
	"""
	response = {
		"status_code": status_code,
		"error": {
			"code": code,
			"message": message,
			"errors": errors or []
        }
    }
	return jsonify(response), status_code

def validate_params():
	"""
	Validates query parameters.
	Returns:
		On Success: Tuple[Dict[str, str], None]: params_dict, None
		On Error: Tuple[None, Dict[str, str]]: None, error_response
	"""
	params = {
		'venue_slug': request.args.get('venue_slug'),
		'cart_value': request.args.get('cart_value'),
		'user_lat': request.args.get('user_lat'), 
		'user_lon': request.args.get('user_lon')
    }
    
	if not all(params.values()):
		return None, make_error(400, ERR_REQUEST, "Missing required parameters", 
			[{"field": f, "details": "This field is required"} for f in params if not params[f]])

	# Validate that parameters have correct types and values
	errors = []
	try:
		params['cart_value'] = int(params['cart_value'])
		params['user_lat'] = float(params['user_lat'])  
		params['user_lon'] = float(params['user_lon'])

		if params['cart_value'] < 0:
			errors.append({"field": "cart_value", "details": "Must be positive"})
		if not -90 <= params['user_lat'] <= 90:
			errors.append({"field": "user_lat", "details": "Must be between -90 and 90"})
		if not -180 <= params['user_lon'] <= 180:
			errors.append({"field": "user_lon", "details": "Must be between -180 and 180"})

	except (ValueError, TypeError) as err:
		return None, make_error(400, ERR_REQUEST, "Invalid numeric values", [{"field": str(err), "details": "Must be a number"}])

	return (None, make_error(400, ERR_REQUEST, "Invalid values", errors)) if errors else (params, None)

def validate_distance_ranges(ranges):
	"""
	Converts distance range values for calculations. Assumes valid structure.
	Returns:
		On Success: Tuple[List[Dict], None]: validated_ranges, None
		On Error: Tuple[None, List[Dict]]: None, errors
	"""
	try:
		return [{'min': float(r['min']), 
				'max': float(r['max']), 
				'a': float(r['a']), 
				'b': float(r['b'])} for r in ranges], []

	except (ValueError, TypeError, KeyError) as err:
		return None, make_error(500, ERR_API, "Invalid JSON data", [{"field": "distance_ranges", "details": "Invalid values"}])

def get_venue_data(venue_slug: str):
	"""
	Fetches venue data from the API and validates it.
	Returns:
		On Success: Tuple[VenueData, None]
    	Oon Error: Tuple[None, ErrorResponse]
	"""
	try:
		static_response = requests.get(f"{BASE_URL}/{venue_slug}/static", timeout=(5, 30)) # import requests, add timeout
		dynamic_response = requests.get(f"{BASE_URL}/{venue_slug}/dynamic", timeout=(5, 30))

		if static_response.status_code != 200 or dynamic_response.status_code != 200:
			code = static_response.status_code if static_response.status_code != 200 else dynamic_response.status_code
			return None, make_error(code, ERR_API, "Failed to fetch data", [
				{"field": "api request", "details": f"Static: {static_response.status_code}, Dynamic: {dynamic_response.status_code}"}])
		
		try:
			static_data = static_response.json()
			dynamic_data = dynamic_response.json()

		except ValueError as err:
			return None, make_error(500, ERR_API, "Invalid JSON response", [{"field": "response", "details": str(err)}])
		
		# SIC! As mentioned in specification: Fields are always present in the response payload if the 
		# response status code is 200, however, we still need to VALIDATE the data for CORRECTNESS:
		errors = []

		# Extract coordinates from the static data:
		try:
			coordinates = static_data['venue_raw']['location']['coordinates']
			venue_lon = float(coordinates[0])
			venue_lat = float(coordinates[1])
			if not -180 <= venue_lon <= 180:
				errors.append({"field": "venue_lon", "details": "Must be between -180 and 180"})
			if not -90 <= venue_lat <= 90:
				errors.append({"field": "venue_lat", "details": "Must be between -90 and 90"})

		except (ValueError, TypeError, IndexError, KeyError) as err:
			errors.append({"field": "coordinates", "details": f"Invalid values: {err}"})
        
		# Extract delivery specs from the dynamic data:
		try:
			order_minimum_no_surcharge = int(dynamic_data['venue_raw']['delivery_specs']['order_minimum_no_surcharge'])
			base_price = int(dynamic_data['venue_raw']['delivery_specs']['delivery_pricing']['base_price'])
			validated_ranges, range_errors = validate_distance_ranges(dynamic_data['venue_raw']['delivery_specs']['delivery_pricing']['distance_ranges'])

			if order_minimum_no_surcharge < 0:
				errors.append({"field": "order_minimum_no_surcharge", "details": "Must be non-negative"})
			if base_price < 0:
				errors.append({"field": "base_price", "details": "Must be non-negative"})
			if range_errors:
				errors.extend(range_errors)

		except (ValueError, TypeError, KeyError) as err:
			errors.append({"field": "delivery_specs", "details": f"Invalid values: {err}"})

		if errors:
			return None, make_error(400, ERR_API, "Invalid data", errors)
	
		venue_data = {
			"venue_lat": venue_lat,
			"venue_lon": venue_lon,
			"order_minimum_no_surcharge": order_minimum_no_surcharge,
			"base_price": base_price,
			"distance_ranges": validated_ranges }

		return venue_data, None

	# See: https://www.geeksforgeeks.org/exception-handling-of-python-requests-module/
	except requests.exceptions.ConnectTimeout as err:
		return None, make_error(408, ERR_CLIENT_TIMEOUT, "Client connection timed out", [{"field": "request", "details": str(err)}])
	except requests.exceptions.ReadTimeout as err:
		return None, make_error(504, ERR_API, "Server response timed out", [{"field": "request", "details": str(err)}])
	except requests.exceptions.ConnectionError as err:
		return None, make_error(503, ERR_API, "Service unavailable", [{"field": "request", "details": str(err)}])
	except requests.exceptions.RequestException as err:
		return None, make_error(500, ERR_API, "Failed to fetch data", [{"field": "request", "details": str(err)}])
	except Exception as err:
		return None, make_error(500, ERR_API, "An unexpected error ocurred during API request", [{"field": "request", "details": str(err)}])

def calculate_distance(user_lat, user_lon, venue_lat, venue_lon):
	"""
	Calculate distance between two coordinates in meters using the Haversine formula:
	https://www.geeksforgeeks.org/haversine-formula-to-find-distance-between-two-points-on-a-sphere/
	Less accurate than the Vincenty formula, but faster and simpler. Enough for calculating smaller distances.
	Returns:
        int: Distance in meters, rounded to nearest integer
	"""
	user = (user_lat, user_lon)
	venue = (venue_lat, venue_lon)
	return round(haversine(user, venue, unit=Unit.METERS))

	# # Alternatively, calculate manually using the formula:
	# import math
	# dLat = (venue_lat - user_lat) * math.pi / 180.0
	# dLon = (venue_lon - user_lon) * math.pi / 180.0

	# # Convert to radians:
	# user_lat = user_lat * math.pi / 180.0
	# venue_lat = venue_lat * math.pi / 180.0

	# # Apply formula:
	# a = (pow(math.sin(dLat / 2), 2) + pow(math.sin(dLon / 2), 2) * math.cos(user_lat) * math.cos(venue_lat))
	# rad = 637100 # Earth radius in meters
	# c = 2 * math.asin(math.sqrt(a))
	# return round(rad * c)

def make_calculations(params: dict, venue_data: dict):
	"""
	Calculates delivery costs including surcharges and fees.
	Returns:
		Tuple[Dict, Optional[Tuple]]: (Response dict, Error response if any)
    """
	small_order_surcharge = max(0, venue_data['order_minimum_no_surcharge'] - params['cart_value'])
    
	distance = int(calculate_distance(params['user_lat'], params['user_lon'], venue_data['venue_lat'], venue_data['venue_lon']))
    
	total_price = 0
	delivery_fee = 0    
	for range in venue_data['distance_ranges']:
		if range['min'] <= distance < range['max'] or (range['max'] == 0 and distance >= range['min']):
			if range['max'] == 0:
				return None, make_error(400, ERR_NO_DELIVERY, "Delivery distance too long", [{"field": "distance", "details": f"{distance} m exceeds max. range of {int(range['min'])} m"}])
			
			delivery_fee = int(venue_data['base_price'] + range['a'] + round(range['b'] * distance / 10))
			total_price = int(params['cart_value'] + delivery_fee + small_order_surcharge)
			break
            
	response = {
		# "DEBUG: venue_slug": params['venue_slug'],
		# "DEBUG: user_lat": params['user_lat'],
		# "DEBUG: user_lon": params['user_lon'],
		# "DEBUG: venue_lat": venue_data['venue_lat'],
		# "DEBUG: venue_lon": venue_data['venue_lon'],
		# "DEBUG: order_minimum_no_surcharge": venue_data['order_minimum_no_surcharge'],
		# "DEBUG: base_price": venue_data['base_price'],
		# "DEBUG: distance_ranges": venue_data['distance_ranges'],
		"total_price": total_price,
		"small_order_surcharge": small_order_surcharge,
		"cart_value": params['cart_value'],
		"delivery": {
			"fee": delivery_fee,
			"distance": distance}
		}
		
	return response, None

@app.route('/api/v1/delivery-order-price')
def calculate_delivery_price():
	"""
    Calculates total delivery price including fees and surcharges.
    Return:
        Tuple[Dict, int]: JSON response and HTTP status code 
    """
	params, error = validate_params()
	if error:
		return error
	
	venue_data, error = get_venue_data(params['venue_slug'])
	if error:
		return error
	
	response, error = make_calculations(params, venue_data)
	if error:
		return error

	return jsonify(response), 200

if __name__ == '__main__':
   app.run(debug=False, port=8000)
