# Delivery Order Price Calculator

REST API service that calculates delivery prices based on cart value, distance, and venue-specific rules.

## Prerequisites

- Python 3.13.1
- pip
- virtualenv

## Installation

1. Navigate to project root folder

2. Create virtual environment:
```bash
python3 -m venv venv
```

3. Activate virtual environment:
```bash
source venv/bin/activate  # MacOS
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies
- Flask==3.1.0
- requests==2.32.3
- haversine==2.9.0
- pytest==8.3.4

Check installed dependencies:
```bash
pip freeze
```

## Usage

1. Start server:
```bash
python3 dopc/app.py
```
Server runs at http://localhost:8000

2. Example API call:
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=example&cart_value=1000&user_lat=60.1699&user_lon=24.9384"
```

## Testing

Run tests:
```bash
python3 -m pytest tests/tests.py -v
```

## Project Structure
```
assignment/
├── dopc/
│   └── app.py          # Main application file
├── tests/
│   └── test.py         # Unit tests
└── requirements.txt
```

## Notes
- Zero order price is valid (items could be paid with coupons)