# Smart Urban Vitality Dashboard

A real-time monitoring dashboard for urban environmental sensors, built with Flask and Chart.js.

## Features

- Real-time monitoring of multiple environmental parameters:
  - Temperature
  - Humidity
  - UV Index
  - Air Quality
  - CO2e Levels
  - Fill Levels
- Interactive charts with multi-station support
- Automatic alerts for critical conditions
- Station location mapping with Google Maps integration
- Detailed sensor logs with filtering capabilities
- Development tools for data management

## Setup Instructions

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

## Configuration

The application is highly configurable through `config.py`:

- `FLASK_ENV`: Set to 'development' or 'production'
- `DEBUG`: Enable/disable debug mode
- `STATIONS`: Configure monitoring stations with names and locations
- `THRESHOLDS`: Set warning thresholds for different parameters
- `UPDATE_INTERVALS`: Configure data refresh rates

## Project Structure

```
.
├── app.py              # Main application file
├── config.py           # Configuration file (not in git)
├── config.template.py  # Configuration template
├── requirements.txt    # Python dependencies
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── logs.html
│   └── station_locations.html
└── static/           # Static files (CSS, JS, etc.)
```

## Development

- The application uses SQLite for development
- Development tools are available in the logs page
- Alert thresholds can be adjusted in `config.py`
- Charts auto-update every 30 seconds by default

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details 