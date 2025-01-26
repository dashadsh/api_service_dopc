# Delivery Order Price Calculator

Delivery Order Price Calculator service (DOPC) - an imaginary backend service which is capable of calculating the total price and price breakdown of a delivery order.
Made on MacOS, tested on Linux.

## Description

When successful request is made, endpoint returns a JSON response in the following format:
```
{
  "total_price": 1190,
  "small_order_surcharge": 0,
  "cart_value": 1000,
  "delivery": {
    "fee": 190,
    "distance": 177
  }
}
```
In case of error, endpoint returns a JSON response in following format:
```
{
  "status_code": 400, 
  "error": {
    "code": "ERR_INVALID_REQUEST_PARAMS", # Machine readable error message
    "message": "Missing required parameters", # Human readable error message
    "errors": [
      {
        "field": "user_lat",  # Parameter causing issue
        "details": "This field is required" # Details about the issue
      },
      {
        "field": "user_lon",
        "details": "This field is required"
      }
    ]
  }
}
```

## Prerequisites

- Python 3.12.3-3.13.1
- pip
- virtualenv


## Project Structure
```
assignment/
├── dopc/
│   └── app.py          # Main application file
├── tests/
│   └── test.py         # Tests
└── requirements.txt
```

## Installation

1. Navigate to the project root folder

2. Create virtual environment:
```bash
python3 -m venv venv
```

3. Activate virtual environment (command valid for MacOS, Linux):
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies:
- Flask
- requests
- haversine
- pytest

## Usage

1. Start server:
```bash
python3 dopc/app.py
```
Server runs at http://localhost:8000

2. Example API call:
```bash
curl http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=60.17094&user_lon=24.93087
```
If using Linux: wrap request in quotes to provide compatibility with bash / stricter zsh (on MacOS quotes can be omitted):
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=60.17094&user_lon=24.93087"
```

3. Additional commands to do API call:
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=60.18094&user_lon=24.93087"
```
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-stockholm&cart_value=10000&user_lat=59.35683&user_lon=18.03150"
```
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-berlin&cart_value=1000&user_lat=52.51032&user_lon=13.45361"
```
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-tokyo&cart_value=700&user_lat=35.65591&user_lon=139.71153"
```

## Testing using Pytest

Open a second terminal, navigate to the root repository. Activate virtual envinroment:
```bash
source venv/bin/activate
```
Run tests:
```bash
python3 -m pytest tests/tests.py -v
```

## Notes
- I assume, zero order price is valid (items could be paid with coupons)

(c) Daria Goremykina
d.goremykina@gmail.com