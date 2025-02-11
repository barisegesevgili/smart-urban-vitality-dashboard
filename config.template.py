# Flask Configuration
FLASK_ENV = 'development'  # Change to 'production' in production environment
DEBUG = True  # Set to False in production

# Database Configuration
DATABASE_URL = 'sqlite:///app.db'  # Replace with your database URL

# Google Maps Configuration
GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'  # Replace with your API key

# Station Configuration
STATIONS = {
    1: {
        'name': 'Station 1',
        'location': {'lat': 0.0000, 'lng': 0.0000}
    },
    # Add more stations as needed
}

# Sensor Thresholds
THRESHOLDS = {
    'temperature': {
        'min': -15,
        'max': 45,
        'warning': 30  # Temperature above this value will trigger a warning
    },
    'humidity': {
        'min': 0,
        'max': 100
    },
    'uv_index': {
        'min': 0,
        'max': 12,
        'warning': 6  # UV index above this value will trigger a warning
    },
    'air_quality': {
        'min': 0,
        'max': 100
    },
    'co2e': {
        'min': 300,
        'max': 1000
    },
    'fill_level': {
        'min': 0,
        'max': 100,
        'warning': 20  # Fill level below this value will trigger a warning
    }
}

# Update Intervals (in milliseconds)
UPDATE_INTERVALS = {
    'charts': 30000,  # 30 seconds
    'alerts': 30000   # 30 seconds
} 