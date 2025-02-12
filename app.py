from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import csv
from io import StringIO

# Initialize Flask app first
app = Flask(__name__)
CORS(app)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/smart_urban_vitality.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Smart Urban Vitality startup')

def load_config():
    """Load configuration from environment variables in production, fall back to config.py in development"""
    current_env = os.environ.get('FLASK_ENV')
    app.logger.info(f'Current FLASK_ENV: {current_env}')
    
    if current_env == 'production':
        try:
            stations_str = os.environ.get('STATIONS', '{}')
            thresholds_str = os.environ.get('THRESHOLDS', '{}')
            update_intervals_str = os.environ.get('UPDATE_INTERVALS', '{}')
            maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            
            # Parse JSON strings, ensuring string keys for stations
            stations_dict = json.loads(stations_str)
            stations = {str(k): v for k, v in stations_dict.items()}
            
            return {
                'FLASK_ENV': current_env,
                'DEBUG': os.environ.get('DEBUG', 'false').lower() == 'true',
                'GOOGLE_MAPS_API_KEY': maps_key,
                'STATIONS': stations,
                'THRESHOLDS': json.loads(thresholds_str),
                'UPDATE_INTERVALS': json.loads(update_intervals_str)
            }
        except json.JSONDecodeError as e:
            app.logger.error(f'Error parsing configuration JSON: {str(e)}')
            # Fallback to empty configurations
            return {
                'FLASK_ENV': 'production',
                'DEBUG': False,
                'GOOGLE_MAPS_API_KEY': '',
                'STATIONS': {
                    "1": {"name": "Englischer Garten", "location": {"lat": 48.1500, "lng": 11.5833}},
                    "2": {"name": "Garching TUM Campus", "location": {"lat": 48.2620, "lng": 11.6670}},
                    "3": {"name": "Garching Mensa", "location": {"lat": 48.2510, "lng": 11.6520}}
                },
                'THRESHOLDS': {},
                'UPDATE_INTERVALS': {'charts': 30000, 'alerts': 30000}
            }
    else:
        try:
            from config import (
                FLASK_ENV, 
                DEBUG, 
                GOOGLE_MAPS_API_KEY, 
                STATIONS, 
                THRESHOLDS,
                UPDATE_INTERVALS
            )
            return {
                'FLASK_ENV': FLASK_ENV,
                'DEBUG': DEBUG,
                'GOOGLE_MAPS_API_KEY': GOOGLE_MAPS_API_KEY,
                'STATIONS': STATIONS,
                'THRESHOLDS': THRESHOLDS,
                'UPDATE_INTERVALS': UPDATE_INTERVALS
            }
        except ImportError:
            # If config.py doesn't exist, use default development values
            return {
                'FLASK_ENV': 'development',
                'DEBUG': True,
                'GOOGLE_MAPS_API_KEY': '',
                'STATIONS': {
                    "1": {"name": "Englischer Garten", "location": {"lat": 48.1500, "lng": 11.5833}},
                    "2": {"name": "Garching TUM Campus", "location": {"lat": 48.2620, "lng": 11.6670}},
                    "3": {"name": "Garching Mensa", "location": {"lat": 48.2510, "lng": 11.6520}}
                },
                'THRESHOLDS': {},
                'UPDATE_INTERVALS': {'charts': 30000, 'alerts': 30000}
            }

config = load_config()
FLASK_ENV = config['FLASK_ENV']
DEBUG = config['DEBUG']
GOOGLE_MAPS_API_KEY = config['GOOGLE_MAPS_API_KEY']
STATIONS = config['STATIONS']
THRESHOLDS = config['THRESHOLDS']
UPDATE_INTERVALS = config['UPDATE_INTERVALS']

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)

# Models
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    air_quality = db.Column(db.Float)
    co2e = db.Column(db.Float)
    fill_level = db.Column(db.Float)
    rtc_time = db.Column(db.DateTime)
    bme_iaq_accuracy = db.Column(db.Integer)
    station_id = db.Column(db.Integer)

# Initialize migrations after model definition
migrate = Migrate(app, db)

# Create tables
with app.app_context():
    try:
        db.create_all()
        app.logger.info('Database tables created successfully')
    except Exception as e:
        app.logger.error(f'Error creating database tables: {str(e)}')

class DatabaseError(Exception):
    pass

class ValidationError(Exception):
    pass

def validate_sensor_data(data):
    required_fields = ['timestamp', 'temperature', 'humidity', 'uv_index', 
                      'air_quality', 'co2e', 'fill_level', 'rtc_time', 
                      'bme_iaq_accuracy', 'station_id']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    try:
        # Handle numeric fields that can be NaN
        float_fields = ['temperature', 'humidity', 'uv_index', 'air_quality', 'co2e', 'fill_level']
        for field in float_fields:
            value = data[field]
            # Check if value is already NaN string
            if isinstance(value, str) and value.upper() == 'NAN':
                data[field] = float('nan')
            else:
                data[field] = float(value)
        
        # These fields must not be NaN
        data['bme_iaq_accuracy'] = int(data['bme_iaq_accuracy'])
        data['station_id'] = int(data['station_id'])
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid data type in fields: {str(e)}")

def format_rtc_time(rtc_time_str):
    try:
        rtc_parts = rtc_time_str.split(' ')
        if len(rtc_parts) != 2:
            raise ValidationError("Invalid RTC time format")
            
        date_parts = rtc_parts[0].split('-')
        time_parts = rtc_parts[1].split(':')
        
        year = int(date_parts[0])
        if year == 0:
            year = datetime.now().year
        
        month = max(1, int(date_parts[1]))
        day = max(1, int(date_parts[2]))
            
        formatted_date = f"{year:04d}-{month:02d}-{day:02d}"
        formatted_time = f"{int(time_parts[0]):02d}:{int(time_parts[1]):02d}:{int(time_parts[2]):02d}"
        rtc_time_str = f"{formatted_date} {formatted_time}"
        
        return datetime.strptime(rtc_time_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, IndexError) as e:
        raise ValidationError(f"Error formatting RTC time: {str(e)}")

# Routes
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f'Error rendering index page: {str(e)}')
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.json
        if not data:
            raise ValidationError("No JSON data received")

        validate_sensor_data(data)
        rtc_time = format_rtc_time(data['rtc_time'])
        
        sensor_data = SensorData(
            timestamp=datetime.fromtimestamp(data['timestamp']),
            temperature=float(data['temperature']),
            humidity=float(data['humidity']),
            uv_index=float(data['uv_index']),
            air_quality=float(data['air_quality']),
            co2e=float(data['co2e']),
            fill_level=float(data['fill_level']),
            rtc_time=rtc_time,
            bme_iaq_accuracy=int(data['bme_iaq_accuracy']),
            station_id=int(data['station_id'])
        )
        
        try:
            db.session.add(sensor_data)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseError(f"Database error: {str(e)}")
            
        app.logger.info(f'Successfully received data from station {data["station_id"]}')
        return jsonify({"status": "success"}), 201
        
    except ValidationError as e:
        app.logger.warning(f'Validation error: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 400
    except DatabaseError as e:
        app.logger.error(f'Database error: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/data', methods=['GET'])
def get_data():
    try:
        app.logger.info('Fetching sensor data for charts')
        sensor_data = SensorData.query.order_by(SensorData.rtc_time.desc()).limit(100).all()
        
        if not sensor_data:
            app.logger.warning('No sensor data found in database')
            return jsonify({
                "stations": STATIONS,
                "data": {},
                "thresholds": THRESHOLDS
            })
            
        # Group data by station_id
        stations_data = {}
        for data in sensor_data:
            station_id = str(data.station_id)  # Convert to string for JSON
            if station_id not in stations_data:
                stations_data[station_id] = []
            
            stations_data[station_id].append({
                "timestamp": data.timestamp.isoformat(),
                "rtc_time": data.rtc_time.isoformat(),
                "temperature": data.temperature,
                "humidity": data.humidity,
                "uv_index": data.uv_index,
                "air_quality": data.air_quality,
                "co2e": data.co2e,
                "fill_level": data.fill_level,
                "bme_iaq_accuracy": data.bme_iaq_accuracy,
                "station_id": data.station_id
            })
        
        app.logger.info(f'Found data for stations: {list(stations_data.keys())}')
        #app.logger.info(f'STATIONS config: {STATIONS}')
        
        response_data = {
            "stations": STATIONS,
            "data": stations_data,
            "thresholds": THRESHOLDS,
            "update_intervals": UPDATE_INTERVALS
        }
        #app.logger.info(f'Sending response: {json.dumps(response_data)}')
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f'Error retrieving sensor data: {str(e)}')
        return jsonify({"status": "error", "message": "Error retrieving data"}), 500

@app.route('/station-locations')
def station_locations():
    try:
        app.logger.info('Accessing station locations page')
        if not GOOGLE_MAPS_API_KEY:
            app.logger.error('Google Maps API key is missing or empty')
            return render_template('station_locations.html',
                                google_maps_api_key='',
                                stations=STATIONS,
                                error_message="Google Maps API key is not configured properly.")
        
        return render_template('station_locations.html', 
                             google_maps_api_key=GOOGLE_MAPS_API_KEY,
                             stations=STATIONS)
    except Exception as e:
        app.logger.error(f'Error rendering station locations page: {str(e)}')
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/sensor_data/<station_id>', methods=['GET'])
def get_sensor_data(station_id):
    try:
        sensor_data = SensorData.query.filter_by(station_id=station_id).order_by(SensorData.rtc_time.desc()).first()
        
        if not sensor_data:
            app.logger.warning(f'No data found for station {station_id}')
            return jsonify({
                "temperature": 0,
                "humidity": 0,
                "uv_index": 0,
                "air_quality": 0,
                "co2e": 0,
                "fill_level": 0,
                "rtc_time": datetime.now().isoformat(),
                "bme_iaq_accuracy": 0,
                "status": "no_data"
            })
            
        data = {
            "timestamp": sensor_data.timestamp.isoformat(),
            "rtc_time": sensor_data.rtc_time.isoformat(),
            "temperature": sensor_data.temperature,
            "humidity": sensor_data.humidity,
            "uv_index": sensor_data.uv_index,
            "air_quality": sensor_data.air_quality,
            "co2e": sensor_data.co2e,
            "fill_level": sensor_data.fill_level,
            "bme_iaq_accuracy": sensor_data.bme_iaq_accuracy,
            "status": "success"
        }
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Error retrieving station data: {str(e)}')
        return jsonify({
            "status": "error",
            "message": f"Error retrieving station data: {str(e)}"
        }), 500

@app.route('/logs')
def logs():
    try:
        return render_template('logs.html', stations=STATIONS)
    except Exception as e:
        app.logger.error(f'Error rendering logs page: {str(e)}')
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/logs_data')
def logs_data():
    try:
        station = request.args.get('station', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        if limit <= 0 or limit > 1000:
            raise ValidationError("Invalid limit parameter")
        
        query = SensorData.query.order_by(SensorData.rtc_time.desc())
        
        if station:
            query = query.filter_by(station_id=station)
        
        sensor_data = query.limit(limit).all()
        
        data = [{
            "id": data.id,
            "timestamp": data.timestamp.isoformat(),
            "rtc_time": data.rtc_time.isoformat(),
            "temperature": data.temperature,
            "humidity": data.humidity,
            "uv_index": data.uv_index,
            "air_quality": data.air_quality,
            "co2e": data.co2e,
            "fill_level": data.fill_level,
            "station_id": data.station_id
        } for data in sensor_data]
        
        return jsonify(data)
        
    except ValidationError as e:
        app.logger.warning(f'Validation error in logs data: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        app.logger.error(f'Error retrieving logs data: {str(e)}')
        return jsonify({"status": "error", "message": "Error retrieving logs data"}), 500

@app.route('/delete_data', methods=['POST'])
def delete_data():
    if FLASK_ENV != 'development':
        return jsonify({"status": "error", "message": "Delete operation only allowed in development environment"}), 403
        
    try:
        if request.content_type == 'application/json':
            data = request.json
            delete_type = data.get('type', 'all')
        else:
            delete_type = request.args.get('type', 'all')
            
        minutes = request.args.get('minutes', type=int)

        if delete_type == 'all':
            # Delete all data
            num_deleted = db.session.query(SensorData).delete()
        elif delete_type == 'older_than' and minutes is not None:
            # Delete data older than specified minutes
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            num_deleted = db.session.query(SensorData).filter(
                SensorData.rtc_time < cutoff_time
            ).delete()
        elif delete_type == 'selected' and 'ids' in request.json:
            # Delete selected logs
            selected_ids = request.json['ids']
            num_deleted = db.session.query(SensorData).filter(
                SensorData.id.in_(selected_ids)
            ).delete(synchronize_session='fetch')
        else:
            raise ValidationError("Invalid delete parameters")

        db.session.commit()
        app.logger.info(f'Successfully deleted {num_deleted} records')
        return jsonify({
            "status": "success",
            "message": f"Successfully deleted {num_deleted} records"
        }), 200

    except ValidationError as e:
        db.session.rollback()
        app.logger.warning(f'Validation error in delete_data: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting data: {str(e)}')
        return jsonify({"status": "error", "message": "Error deleting data"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/export_csv')
def export_csv():
    try:
        # Query all sensor data
        sensor_data = SensorData.query.order_by(SensorData.rtc_time.desc()).all()
        
        if not sensor_data:
            return jsonify({"status": "error", "message": "No data to export"}), 404

        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write headers
        writer.writerow([
            'Timestamp', 'RTC Time', 'Station ID', 'Temperature (°C)', 
            'Humidity (%)', 'UV Index', 'Air Quality (%)', 
            'CO2e (ppm)', 'Fill Level (%)', 'BME IAQ Accuracy'
        ])
        
        # Write data
        for data in sensor_data:
            writer.writerow([
                data.timestamp.isoformat(),
                data.rtc_time.isoformat(),
                data.station_id,
                data.temperature,
                data.humidity,
                data.uv_index,
                data.air_quality,
                data.co2e,
                data.fill_level,
                data.bme_iaq_accuracy
            ])
        
        # Prepare the response
        output = si.getvalue()
        si.close()
        
        return output, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=sensor_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
        
    except Exception as e:
        app.logger.error(f'Error exporting CSV: {str(e)}')
        return jsonify({"status": "error", "message": "Error generating CSV"}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG)