import pytest
import json
from datetime import datetime, UTC

def test_validation_error_on_invalid_content_type(client):
    """Test that non-JSON content type raises proper error."""
    response = client.post('/api/sensor-data', 
                         data='not json data',
                         content_type='text/plain')
    assert response.status_code == 415
    assert 'error' in response.json
    assert 'Content-Type' in response.json['error']

def test_validation_error_on_invalid_query_params(client):
    """Test that invalid query parameters raise proper error."""
    response = client.get('/api/sensor-data?station_id=1;drop%20table%20users')
    assert response.status_code == 400
    assert 'error' in response.json
    assert 'Invalid query parameter' in response.json['error']

def test_resource_not_found_error(client):
    """Test that requesting non-existent data returns 404."""
    response = client.get('/api/sensor-data?station_id=999')
    assert response.status_code == 404
    assert 'error' in response.json
    assert 'No data found' in response.json['error']

def test_validation_error_on_missing_required_field(client):
    """Test that missing required fields raise proper error."""
    data = {
        'temperature': 25.5,
        # Missing other required fields
    }
    response = client.post('/api/sensor-data',
                         json=data,
                         content_type='application/json')
    assert response.status_code == 400
    assert 'error' in response.json

def test_successful_data_addition(client):
    """Test that valid data is still processed correctly."""
    data = {
        'timestamp': datetime.now(UTC).isoformat(),
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
                         json=data,
                         content_type='application/json')
    assert response.status_code == 201
    assert 'message' in response.json
    assert response.json['message'] == 'Data added successfully'

def test_database_rollback_on_error(client, db):
    """Test that database is rolled back on error."""
    initial_count = db.session.query(db.Model.metadata.tables['sensor_data']).count()
    
    # Send invalid data that will pass initial validation but fail database insert
    data = {
        'timestamp': datetime.now(UTC).isoformat(),
        'temperature': 25.5,
        'humidity': 60.0,
        'uv_index': 5.0,
        'air_quality': 80.0,
        'co2e': 400.0,
        'fill_level': 75.0,
        'rtc_time': '2024-02-14 12:00:00',
        'bme_iaq_accuracy': 'invalid',  # Should be int
        'station_id': 1
    }
    response = client.post('/api/sensor-data',
                         json=data,
                         content_type='application/json')
    
    assert response.status_code == 400
    # Verify no records were added
    final_count = db.session.query(db.Model.metadata.tables['sensor_data']).count()
    assert final_count == initial_count

def test_csv_export_with_valid_data(client):
    """Test that CSV export still works with valid data."""
    # First add some test data
    data = {
        'timestamp': datetime.now(UTC).isoformat(),
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
               json=data,
               content_type='application/json')

    # Now try to export it
    response = client.get('/api/export-csv?station_id=1')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
    assert 'sensor_data_station_1.csv' in response.headers['Content-Disposition']

def test_health_check_still_works(client):
    """Test that health check endpoint still works."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy' 