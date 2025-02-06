from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
from config import (
    FLASK_ENV, 
    DEBUG, 
    GOOGLE_MAPS_API_KEY, 
    STATIONS, 
    THRESHOLDS,
    UPDATE_INTERVALS
)

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

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class DatabaseError(Exception):
    pass

class ValidationError(Exception):
    pass

# Models
class SensorData(db.Model):
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

def validate_sensor_data(data):
    required_fields = ['timestamp', 'temperature', 'humidity', 'uv_index', 
                      'air_quality', 'co2e', 'fill_level', 'rtc_time', 
                      'bme_iaq_accuracy', 'station_id']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    try:
        float(data['temperature'])
        float(data['humidity'])
        float(data['uv_index'])
        float(data['air_quality'])
        float(data['co2e'])
        float(data['fill_level'])
        int(data['bme_iaq_accuracy'])
        int(data['station_id'])
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
        return jsonify({
            "stations": STATIONS,
            "data": stations_data,
            "thresholds": THRESHOLDS,
            "update_intervals": UPDATE_INTERVALS
        })
        
    except Exception as e:
        app.logger.error(f'Error retrieving sensor data: {str(e)}')
        return jsonify({"status": "error", "message": "Error retrieving data"}), 500

@app.route('/station-locations')
def station_locations():
    try:
        app.logger.info('Accessing station locations page')
        return render_template('station_locations.html', 
                             google_maps_api_key=GOOGLE_MAPS_API_KEY,
                             stations=STATIONS)
    except Exception as e:
        app.logger.error(f'Error rendering station locations page: {str(e)}')
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/sensor_data/<station_id>', methods=['GET'])
def get_sensor_data(station_id):
    try:
        app.logger.info(f'Fetching data for station {station_id}')
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
        app.logger.info(f'Successfully retrieved data for station {station_id}')
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
        return render_template('logs.html')
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
        delete_type = request.args.get('type', 'all')
        days = request.args.get('days', type=int)

        if delete_type == 'all':
            # Delete all data
            num_deleted = db.session.query(SensorData).delete()
        elif delete_type == 'older_than' and days is not None:
            # Delete data older than specified days
            cutoff_date = datetime.now() - timedelta(days=days)
            num_deleted = db.session.query(SensorData).filter(
                SensorData.rtc_time < cutoff_date
            ).delete()
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

if __name__ == '__main__':
    app.run(debug=DEBUG)