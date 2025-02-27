from datetime import datetime, UTC
from app.models.sensor_data import SensorData

def test_new_sensor_data(db):
    """Test creating a new sensor data entry."""
    now = datetime.now(UTC)
    sensor_data = SensorData(
        timestamp=now,
        temperature=25.5,
        humidity=60.0,
        uv_index=5.0,
        air_quality=80.0,
        co2e=400.0,
        fill_level=75.0,
        rtc_time=now,
        bme_iaq_accuracy=3,
        station_id=1
    )
    db.session.add(sensor_data)
    db.session.commit()

    assert sensor_data.id is not None
    assert sensor_data.temperature == 25.5
    assert sensor_data.humidity == 60.0
    assert sensor_data.station_id == 1

def test_sensor_data_timestamp_default(db):
    """Test that timestamp gets default value."""
    sensor_data = SensorData(
        temperature=25.5,
        humidity=60.0,
        uv_index=5.0,
        air_quality=80.0,
        co2e=400.0,
        fill_level=75.0,
        bme_iaq_accuracy=3,
        station_id=1
    )
    db.session.add(sensor_data)
    db.session.commit()

    assert sensor_data.timestamp is not None
    assert sensor_data.timestamp.tzinfo is not None  # Verify it's timezone-aware 