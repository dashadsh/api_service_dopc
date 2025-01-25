# Delivery Order Price Calculator

REST API service that calculates delivery prices based on cart value, distance, and venue-specific rules.
Made on MacOS, tested on Linux.

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
│   └── test.py         # Unit tests
└── requirements.txt
```

## Installation

1. Navigate to project root folder

2. Create virtual environment:
```bash
python3 -m venv venv
```

3. Activate virtual environment:
```bash
source venv/bin/activate  # MacOS, Linux
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies
- Flask
- requests
- haversine
- pytest

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
Linux: wrap request as was made abowe in quotes to provide compatibility with bash / stricter zsh
MacOS: quotes can be omitted

## Testing

Open a second terminal, navigate to the root repository.
Activate virtual envinroment.
Run tests:
```bash
source venv/bin/activate
python3 -m pytest tests/tests.py -v
```

## Notes
- Zero order price is valid (items could be paid with coupons)