from flask import jsonify, render_template, request, send_file
from datetime import datetime, timedelta, UTC
import csv
from io import StringIO, BytesIO
from flask_apispec import use_kwargs, marshal_with, doc
from marshmallow import fields
from ..models.sensor_data import db, SensorData
from ..utils.validators import validate_sensor_data, format_rtc_time
from ..schemas import SensorDataSchema, sensor_data_response, success_response
from flask_limiter.util import get_remote_address
from ..utils.errors import ValidationError, ResourceNotFoundError
import re

def register_routes(app):
    limiter = app.limiter

    @app.before_request
    def validate_content_type():
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                raise ValidationError('Content-Type must be application/json', status_code=415)
            
        # Validate query parameters against SQL injection
        for key, value in request.args.items():
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', str(value)):
                raise ValidationError('Invalid query parameter')

    @app.route('/')
    @limiter.exempt
    def index():
        return render_template('index.html',
                            GOOGLE_MAPS_API_KEY=app.config['GOOGLE_MAPS_API_KEY'],
                            GOOGLE_MAPS_MAP_ID=app.config['GOOGLE_MAPS_MAP_ID'],
                            STATIONS=app.config['STATIONS'],
                            THRESHOLDS=app.config['THRESHOLDS'],
                            UPDATE_INTERVALS=app.config['UPDATE_INTERVALS'])

    @app.route('/api/sensor-data', methods=['POST'])
    @limiter.limit("100 per minute")
    @doc(description='Add new sensor data.',
         tags=['Sensor Data'])
    def add_sensor_data():
        """Add new sensor data to the database."""
        data = request.get_json()
        if not data:
            raise ValidationError('No data provided')

        validate_sensor_data(data)
        rtc_time = format_rtc_time(data['rtc_time'])
        
        try:
            sensor_data = SensorData(
                timestamp=datetime.now(UTC),
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
            
            db.session.add(sensor_data)
            db.session.commit()
            
            return {'message': 'Data added successfully'}, 201
            
        except (ValueError, TypeError) as e:
            db.session.rollback()
            raise ValidationError(f'Invalid data type: {str(e)}')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding sensor data: {str(e)}')
            raise

    @app.route('/api/sensor-data', methods=['GET'])
    @limiter.limit("200 per minute")
    @doc(description='Get sensor data for a specific station.',
         tags=['Sensor Data'])
    def get_sensor_data():
        """Get sensor data for a specific station."""
        station_id = request.args.get('station_id', type=int)
        hours = request.args.get('hours', 24, type=int)
        
        if not station_id:
            raise ValidationError('station_id is required')
            
        time_threshold = datetime.now(UTC) - timedelta(hours=hours)
        
        query = SensorData.query.filter(
            SensorData.station_id == station_id,
            SensorData.timestamp >= time_threshold
        ).order_by(SensorData.timestamp.asc())
        
        result = query.all()
        if not result:
            raise ResourceNotFoundError(f'No data found for station {station_id}')
        
        schema = SensorDataSchema(many=True)
        return schema.dump(result)

    @app.route('/api/export-csv', methods=['GET'])
    @limiter.limit("100 per hour")
    @doc(description='Export sensor data as CSV.',
         tags=['Sensor Data'])
    def export_csv():
        """Export sensor data as CSV."""
        station_id = request.args.get('station_id', type=int)
        hours = request.args.get('hours', 24, type=int)
        
        if not station_id:
            raise ValidationError('station_id is required')
            
        time_threshold = datetime.now(UTC) - timedelta(hours=hours)
        
        query = SensorData.query.filter(
            SensorData.station_id == station_id,
            SensorData.timestamp >= time_threshold
        ).order_by(SensorData.timestamp.asc())
        
        result = query.all()
        if not result:
            raise ResourceNotFoundError(f'No data found for station {station_id}')
        
        # Create string buffer first
        string_buffer = StringIO()
        writer = csv.writer(string_buffer)
        
        # Write headers
        writer.writerow(['timestamp', 'temperature', 'humidity', 'uv_index', 
                       'air_quality', 'co2e', 'fill_level', 'rtc_time', 
                       'bme_iaq_accuracy'])
        
        # Write data
        for record in result:
            writer.writerow([
                record.timestamp.isoformat(),
                record.temperature,
                record.humidity,
                record.uv_index,
                record.air_quality,
                record.co2e,
                record.fill_level,
                record.rtc_time.isoformat() if record.rtc_time else None,
                record.bme_iaq_accuracy
            ])
        
        # Convert to bytes
        output = BytesIO()
        output.write(string_buffer.getvalue().encode('utf-8-sig'))
        output.seek(0)
        string_buffer.close()
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sensor_data_station_{station_id}.csv'
        )

    @app.route('/health')
    @limiter.exempt
    @doc(description='Health check endpoint.',
         tags=['System'])
    def health_check():
        """Check if the API is healthy."""
        return {'status': 'healthy'}
