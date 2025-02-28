# Smart Urban Vitality Dashboard

Welcome to the Smart Urban Vitality Dashboard! 👋 This is your go-to solution for monitoring urban environmental conditions in real-time. Built with Flask and Chart.js, our dashboard brings environmental sensor data to life with beautiful visualizations and intuitive controls.


## ATTENTION!
As we have a free subscription of the Render application, the server goes down after a while, it does not receive any requests. So expect to wait some time till the server comes up again, after you make your first request.

## What's Inside? 🎯

Our dashboard helps you keep an eye on:
- 🌡️ Temperature
- 💧 Humidity
- ☀️ UV Index
- 🌬️ Air Quality
- 🏭 CO2e Levels
- 📊 Fill Levels

Plus, you get:
- 📈 Live-updating charts that track multiple stations
- 🗺️ Interactive Google Maps integration
- 📱 Mobile-friendly design
- 🔍 Powerful data filtering and export tools
- 🛡️ Built-in data validation and error handling
- 🔄 Automatic rate limiting for API protection
- 📊 CSV export functionality

## Getting Started 🚀

### Setting Up Your Development Environment

1. First, grab the code:
```bash
git clone https://github.com/barisegesevgili/smart-urban-vitality-dashboard.git
cd smart-urban-vitality-dashboard
```

2. Set up your Python environment:
```bash
# For Mac/Linux users
python3 -m venv venv
source venv/bin/activate

# For Windows users
python -m venv venv
.\venv\Scripts\activate
```

3. Install what you need:
```bash
pip install -r requirements.txt
```

4. Set up your config:
```bash
cp config.template.py config.py
```

Now, open `config.py` and add:
- Your Google Maps API key
- Your Map ID (you can create one in Google Cloud Console)
- Your station locations
- Any custom thresholds you want
- How often you want the data to update

5. Get your database ready:
```bash
flask db upgrade
```

6. Fire it up!
```bash
flask run
```

Visit `http://localhost:5000` to see your dashboard in action! 🎉

### Going Live 🌐

Ready to deploy? Here's what you need:

1. Essential environment variables:
   - `FLASK_ENV`: Set this to 'production'
   - `DEBUG`: Keep this 'false' in production
   - `GOOGLE_MAPS_API_KEY`: Your Maps API key
   - `GOOGLE_MAPS_MAP_ID`: Your custom map style ID
   - `SECRET_KEY`: Keep this secret and secure!
   - `STATIONS`: Your station config in JSON

2. Setting up on Render:
   - Head to your Render dashboard
   - Add your environment variables
   - Make sure your Google Cloud Project has the right APIs enabled
   - Double-check your API key permissions

3. Example station setup:
```json
{
    "1": {
        "name": "Garching/IOT-Lab",
        "location": {"lat": 48.26264036847362, "lng": 11.668331022751858}
    },
    "2": {
        "name": "Garching/Basketball Court",
        "location": {"lat": 48.26364466819253, "lng": 11.668459013506432}
    },
    "3": {
        "name": "Garching/IOT-Lab Balcony",
        "location": {"lat": 48.26271268490997, "lng": 11.66840813626192}
    }
}
```

## API Quick Guide 📚

Need to interact with the data programmatically? We've got you covered:

- `POST /api/sensor-data`: Add new sensor readings
- `GET /api/sensor-data`: Fetch sensor data (with optional filters)
- `GET /api/export-csv`: Download data as CSV
- `GET /health`: Quick system health check

All endpoints are rate-limited to protect the service. The limits are:
- 10,000 requests per day
- 1,000 requests per hour
- Specific endpoints may have additional limits

## Project Layout 📁

Here's how everything is organized:
```
.
├── app/               # Main application package
│   ├── models/       # Database models
│   ├── routes/       # API endpoints
│   ├── utils/        # Helper functions
│   ├── templates/    # HTML templates
│   └── schemas.py    # Data validation schemas
├── tests/            # Test suite
├── migrations/       # Database migrations
├── logs/            # Application logs
├── instance/        # Instance-specific files
├── app.py           # Application entry point
├── config.py        # Configuration (not in git)
├── requirements.txt  # Python dependencies
└── gunicorn.conf.py # Production server config
```

## Under the Hood 🔧

We're using SQLAlchemy with this data structure:
```python
class SensorData:
    - timestamp: DateTime      # When did we get the reading?
    - temperature: Float      # How hot/cold is it?
    - humidity: Float        # How humid is it?
    - uv_index: Float       # How sunny is it?
    - air_quality: Float    # How clean is the air?
    - co2e: Float          # Carbon dioxide equivalent
    - fill_level: Float    # How full is it?
    - rtc_time: DateTime   # Device's time
    - bme_iaq_accuracy: Integer  # How accurate is the reading?
    - station_id: Integer  # Which station is this?
```

## Testing 🧪

Run the test suite with:
```bash
pytest
```

Our tests cover:
- Data models
- API endpoints
- Validation logic
- Error handling
- CSV export functionality

## Want to Help? 🤝

Send good vibes and maybe a pull request! 

## License 📜

This project is under the BES License - catch me in München for the details! 🍺

---

Made with ❤️ at TUM 
