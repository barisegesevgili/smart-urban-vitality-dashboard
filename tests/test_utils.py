import pytest
from datetime import datetime
from app.utils.validators import (
    convert_air_quality_to_percent,
    validate_sensor_data,
    format_rtc_time,
    ValidationError
)

def test_convert_air_quality_to_percent():
    """Test air quality conversion function."""
    assert convert_air_quality_to_percent(0) == 100.0
    assert convert_air_quality_to_percent(250) == 50.0
    assert convert_air_quality_to_percent(500) == 0.0
    assert convert_air_quality_to_percent(-1) == -1

def test_validate_sensor_data_valid():
    """Test validation with valid data."""
    data = {
        'timestamp': '2024-02-14T12:00:00',
        'temperature': '25.5',
        'humidity': '60.0',
        'uv_index': '5.0',
        'air_quality': '80.0',
        'co2e': '400.0',
        'fill_level': '75.0',
        'rtc_time': '2024-02-14 12:00:00',
        'bme_iaq_accuracy': '3',
        'station_id': '1'
    }
    validate_sensor_data(data)  # Should not raise any exception

def test_validate_sensor_data_missing_field():
    """Test validation with missing field."""
    data = {
        'temperature': '25.5',
        'humidity': '60.0'
    }
    with pytest.raises(ValidationError):
        validate_sensor_data(data)

def test_validate_sensor_data_invalid_type():
    """Test validation with invalid data type."""
    data = {
        'timestamp': '2024-02-14T12:00:00',
        'temperature': 'invalid',
        'humidity': '60.0',
        'uv_index': '5.0',
        'air_quality': '80.0',
        'co2e': '400.0',
        'fill_level': '75.0',
        'rtc_time': '2024-02-14 12:00:00',
        'bme_iaq_accuracy': '3',
        'station_id': '1'
    }
    with pytest.raises(ValidationError):
        validate_sensor_data(data)

def test_format_rtc_time_valid():
    """Test RTC time formatting with valid input."""
    rtc_time = format_rtc_time('2024-02-14 12:00:00')
    assert isinstance(rtc_time, datetime)
    assert rtc_time.year == 2024
    assert rtc_time.month == 2
    assert rtc_time.day == 14

def test_format_rtc_time_invalid():
    """Test RTC time formatting with invalid input."""
    with pytest.raises(ValidationError):
        format_rtc_time('invalid_time_format') 