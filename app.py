from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    sensor_data = SensorData(
        timestamp=datetime.fromtimestamp(data['timestamp']),
        temperature=data['temperature'],
        humidity=data['humidity'],
        uv_index=data['uv_index'],
        air_quality=data['air_quality'],
        co2e=data['co2e'],
        fill_level=data['fill_level'],
        rtc_time=datetime.fromtimestamp(data['rtc_time']),
        bme_iaq_accuracy=data['bme_iaq_accuracy'],
        station_id=data['station_id']
    )
    db.session.add(sensor_data)
    db.session.commit()
    return jsonify({"status": "success"}), 201

@app.route('/data', methods=['GET'])
def get_data():
    sensor_data = SensorData.query.order_by(SensorData.timestamp.desc()).limit(100).all()
    data = [{
        "timestamp": data.timestamp.isoformat(),
        "temperature": data.temperature,
        "humidity": data.humidity,
        "uv_index": data.uv_index,
        "air_quality": data.air_quality,
        "co2e": data.co2e,
        "fill_level": data.fill_level,
        "rtc_time": data.rtc_time.isoformat(),
        "bme_iaq_accuracy": data.bme_iaq_accuracy,
        "station_id": data.station_id
    } for data in sensor_data]
    return jsonify(data)

@app.route('/station-locations')
def station_locations():
    return render_template('station_locations.html')

@app.route('/go-to-station-locations')
def go_to_station_locations():
    return redirect(url_for('station_locations'))

@app.route('/sensor_data/<station_id>', methods=['GET'])
def get_sensor_data(station_id):
    sensor_data = SensorData.query.filter_by(station_id=station_id).order_by(SensorData.timestamp.desc()).first()
    if sensor_data:
        data = {
            "timestamp": sensor_data.timestamp.isoformat(),
            "temperature": sensor_data.temperature,
            "humidity": sensor_data.humidity,
            "uv_index": sensor_data.uv_index,
            "air_quality": sensor_data.air_quality,
            "co2e": sensor_data.co2e,
            "fill_level": sensor_data.fill_level,
            "rtc_time": sensor_data.rtc_time.isoformat(),
            "bme_iaq_accuracy": sensor_data.bme_iaq_accuracy
        }
        return jsonify(data)
    return jsonify({"error": "No data found for this station"}), 404

if __name__ == '__main__':
    app.run(debug=True)