from datetime import datetime, UTC
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TypeDecorator, DateTime

class UTCDateTime(TypeDecorator):
    """Automatically convert naive datetime to UTC."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.replace(tzinfo=UTC)
        return value

db = SQLAlchemy()

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(UTCDateTime, nullable=False, default=lambda: datetime.now(UTC))
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    air_quality = db.Column(db.Float)
    co2e = db.Column(db.Float)
    fill_level = db.Column(db.Float)
    rtc_time = db.Column(UTCDateTime)
    bme_iaq_accuracy = db.Column(db.Integer)
    station_id = db.Column(db.Integer) 