import json
from datetime import datetime

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_add_sensor_data_valid(client):
    """Test adding valid sensor data."""
    data = {
        'timestamp': '2024-02-14T12:00:00',
        'temperature': 25.5,
        'humidity': 60.0,
        'uv_index': 5.0,
        'air_quality': 80.0,
        'co2e': 400.0,
        'fill_level': 75.0,
        'rtc_time': '2024-02-14 12:00:00',
        'bme_iaq_accuracy': 3,
        'station_id': 1
    }
    response = client.post('/api/sensor-data',
                         data=json.dumps(data),
                         content_type='application/json')
    assert response.status_code == 201
    assert 'message' in response.json

def test_add_sensor_data_invalid(client):
    """Test adding invalid sensor data."""
    data = {
        'temperature': 25.5  # Missing required fields
    }
    response = client.post('/api/sensor-data',
                         data=json.dumps(data),
                         content_type='application/json')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_sensor_data(client, db):
    """Test getting sensor data."""
    # First add some test data
    data = {
        'timestamp': '2024-02-14T12:00:00',
        'temperature': 25.5,
        'humidity': 60.0,
        'uv_index': 5.0,
        'air_quality': 80.0,
        'co2e': 400.0,
        'fill_level': 75.0,
        'rtc_time': '2024-02-14 12:00:00',
        'bme_iaq_accuracy': 3,
        'station_id': 1
    }
    client.post('/api/sensor-data',
               data=json.dumps(data),
               content_type='application/json')

    # Now get the data
    response = client.get('/api/sensor-data?station_id=1')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    if len(response.json) > 0:
        assert 'temperature' in response.json[0]
        assert 'humidity' in response.json[0]

def test_get_sensor_data_missing_station(client):
    """Test getting sensor data without station_id."""
    response = client.get('/api/sensor-data')
    assert response.status_code == 400
    assert 'error' in response.json

def test_export_csv(client, db):
    """Test CSV export functionality."""
    # First add some test data
    data = {
        'timestamp': '2024-02-14T12:00:00',
        'temperature': 25.5,
        'humidity': 60.0,
        'uv_index': 5.0,
        'air_quality': 80.0,
        'co2e': 400.0,
        'fill_level': 75.0,
        'rtc_time': '2024-02-14 12:00:00',
        'bme_iaq_accuracy': 3,
        'station_id': 1
    }
    client.post('/api/sensor-data',
               data=json.dumps(data),
               content_type='application/json')

    # Now export the data
    response = client.get('/api/export-csv?station_id=1')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
    assert 'sensor_data_station_1.csv' in response.headers['Content-Disposition'] 