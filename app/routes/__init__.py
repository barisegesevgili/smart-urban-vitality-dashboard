from flask import jsonify, render_template, request, send_file
from datetime import datetime, timedelta, UTC
import csv
from io import StringIO, BytesIO
from ..models.sensor_data import db, SensorData
from ..utils.validators import validate_sensor_data, format_rtc_time, ValidationError

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html',
                            GOOGLE_MAPS_API_KEY=app.config['GOOGLE_MAPS_API_KEY'],
                            GOOGLE_MAPS_MAP_ID=app.config['GOOGLE_MAPS_MAP_ID'],
                            STATIONS=app.config['STATIONS'],
                            THRESHOLDS=app.config['THRESHOLDS'],
                            UPDATE_INTERVALS=app.config['UPDATE_INTERVALS'])

    @app.route('/api/sensor-data', methods=['POST'])
    def add_sensor_data():
        try:
            data = request.get_json()
            validate_sensor_data(data)
            
            # Format RTC time
            rtc_time = format_rtc_time(data['rtc_time'])
            
            sensor_data = SensorData(
                timestamp=datetime.now(UTC),
                temperature=data['temperature'],
                humidity=data['humidity'],
                uv_index=data['uv_index'],
                air_quality=data['air_quality'],
                co2e=data['co2e'],
                fill_level=data['fill_level'],
                rtc_time=rtc_time,
                bme_iaq_accuracy=data['bme_iaq_accuracy'],
                station_id=data['station_id']
            )
            
            db.session.add(sensor_data)
            db.session.commit()
            
            return jsonify({'message': 'Data added successfully'}), 201
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f'Error adding sensor data: {str(e)}')
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/sensor-data', methods=['GET'])
    def get_sensor_data():
        try:
            station_id = request.args.get('station_id', type=int)
            hours = request.args.get('hours', 24, type=int)
            
            if not station_id:
                return jsonify({'error': 'station_id is required'}), 400
                
            time_threshold = datetime.now(UTC) - timedelta(hours=hours)
            
            query = SensorData.query.filter(
                SensorData.station_id == station_id,
                SensorData.timestamp >= time_threshold
            ).order_by(SensorData.timestamp.asc())
            
            data = []
            for record in query.all():
                data.append({
                    'timestamp': record.timestamp.isoformat(),
                    'temperature': record.temperature,
                    'humidity': record.humidity,
                    'uv_index': record.uv_index,
                    'air_quality': record.air_quality,
                    'co2e': record.co2e,
                    'fill_level': record.fill_level,
                    'rtc_time': record.rtc_time.isoformat() if record.rtc_time else None,
                    'bme_iaq_accuracy': record.bme_iaq_accuracy
                })
            
            return jsonify(data)
            
        except Exception as e:
            app.logger.error(f'Error retrieving sensor data: {str(e)}')
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/export-csv', methods=['GET'])
    def export_csv():
        try:
            station_id = request.args.get('station_id', type=int)
            hours = request.args.get('hours', 24, type=int)
            
            if not station_id:
                return jsonify({'error': 'station_id is required'}), 400
                
            time_threshold = datetime.now(UTC) - timedelta(hours=hours)
            
            query = SensorData.query.filter(
                SensorData.station_id == station_id,
                SensorData.timestamp >= time_threshold
            ).order_by(SensorData.timestamp.asc())
            
            # Create string buffer first
            string_buffer = StringIO()
            writer = csv.writer(string_buffer)
            
            # Write headers
            writer.writerow(['timestamp', 'temperature', 'humidity', 'uv_index', 
                           'air_quality', 'co2e', 'fill_level', 'rtc_time', 
                           'bme_iaq_accuracy'])
            
            # Write data
            for record in query.all():
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
            output.write(string_buffer.getvalue().encode('utf-8-sig'))  # Use UTF-8 with BOM for Excel compatibility
            output.seek(0)
            string_buffer.close()
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'sensor_data_station_{station_id}.csv'
            )
            
        except Exception as e:
            app.logger.error(f'Error exporting CSV: {str(e)}')
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'})
