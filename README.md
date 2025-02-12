# Smart Urban Vitality Dashboard

A real-time monitoring dashboard for urban environmental sensors, built with Flask and Chart.js. This application collects and visualizes environmental data from IoT sensors deployed across various locations.

## Features

- Real-time monitoring of multiple environmental parameters:
  - Temperature
  - Humidity
  - UV Index
  - Air Quality
  - CO2e Levels (Carbon Dioxide Equivalent)
  - Fill Levels
- Interactive charts with multi-station support and real-time updates
- Automatic data validation and error handling
- Station location mapping with Google Maps integration
- Detailed sensor logs with filtering and export capabilities
- Development tools for data management and debugging
- RESTful API endpoints for data ingestion and retrieval
- Configurable alert thresholds for environmental parameters

## Setup Instructions

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/barisegesevgili/smart-urban-vitality-dashboard.git
cd smart-urban-vitality-dashboard
```

2. Create and activate virtual environment:
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
```bash
cp config.template.py config.py
```
Edit `config.py` with your settings:
- Add your Google Maps API key
- Add your Google Maps Map ID (create one in Google Cloud Console)
- Configure station locations
- Adjust sensor thresholds
- Set update intervals

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

The dashboard will be available at `http://localhost:5000`

### Deployment Configuration

The application is configured to run on Render or similar platforms. Required environment variables:

1. Required Environment Variables:
   - `FLASK_ENV`: Set to 'production'
   - `DEBUG`: Set to 'false'
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `GOOGLE_MAPS_MAP_ID`: Your Google Maps Map ID (for custom map styling)
   - `SECRET_KEY`: A secure secret key for the application
   - `STATIONS`: JSON configuration for your monitoring stations

2. Setting up Google Maps on Render:
   - Go to your Render dashboard
   - Navigate to the Environment Variables section
   - Add both `GOOGLE_MAPS_API_KEY` and `GOOGLE_MAPS_MAP_ID`
   - Ensure your Google Cloud Project has the following APIs enabled:
     - Maps JavaScript API
     - Maps Styling API (for custom map styles)
   - Make sure your API key has the necessary permissions for these services

3. Example STATIONS configuration:
```json
{
    1: {
        'name': 'Garching/IOT-Lab',
        'location': {'lat': 48.26264036847362, 'lng': 11.668331022751858}
    },
    2: {
        'name': 'Garching/Basketball Court',
        'location': {'lat': 48.26364466819253, 'lng': 11.668459013506432}
    },
    3: {
        'name': 'Garching/IOT-Lab Balcony',
        'location': {'lat': 48.26271268490997, 'lng': 11.66840813626192}
    }
}
```

## API Endpoints

- `POST /data`: Submit new sensor data
- `GET /data`: Retrieve sensor data with optional filtering
- `GET /station-locations`: Get all station locations
- `GET /sensor_data/<station_id>`: Get data for a specific station
- `GET /logs`: View system logs
- `GET /export_csv`: Export sensor data as CSV
- `GET /health`: System health check

## Project Structure

```
.
├── app.py              # Main application file
├── config.py           # Configuration file (not in git)
├── config.template.py  # Configuration template
├── requirements.txt    # Python dependencies
├── gunicorn.conf.py   # Gunicorn configuration
├── render.yaml        # Render deployment configuration
├── migrations/        # Database migrations
├── logs/             # Application logs
├── templates/        # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── logs.html
│   └── station_locations.html
└── instance/         # Instance-specific files (SQLite database)
```

## Development Features

- SQLite database for development with automatic migrations
- Comprehensive logging system with rotation
- Development tools available in the logs page
- Configurable alert thresholds
- Auto-updating charts (default: 30 seconds)
- Data validation and sanitization
- Error handling and debugging support

## Data Model

The application uses SQLAlchemy with the following main model:

```python
class SensorData:
    - timestamp: DateTime
    - temperature: Float
    - humidity: Float
    - uv_index: Float
    - air_quality: Float
    - co2e: Float
    - fill_level: Float
    - rtc_time: DateTime
    - bme_iaq_accuracy: Integer
    - station_id: Integer
```

## Contributing

1. Send good wishes

## License

This project is licensed under the BES License - see me at München for details 