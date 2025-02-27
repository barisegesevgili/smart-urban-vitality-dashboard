from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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