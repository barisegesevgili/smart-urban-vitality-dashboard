from datetime import datetime

class DatabaseError(Exception):
    pass

class ValidationError(Exception):
    pass

def convert_air_quality_to_percent(score):
    """Convert air quality score (0-500) to percentage (0-100)"""
    if score < 0:
        return -1
    return 100.0 * (1.0 - (score / 500))

def validate_sensor_data(data):
    required_fields = ['timestamp', 'temperature', 'humidity', 'uv_index', 
                      'air_quality', 'co2e', 'fill_level', 'rtc_time', 
                      'bme_iaq_accuracy', 'station_id']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    try:
        # Handle numeric fields that can be NaN
        float_fields = ['temperature', 'humidity', 'uv_index', 'co2e', 'fill_level']
        for field in float_fields:
            value = data[field]
            # Check if value is already NaN string
            if isinstance(value, str) and value.upper() == 'NAN':
                data[field] = float('nan')
            else:
                data[field] = float(value)
        
        # Special handling for air_quality - convert score to percentage
        if isinstance(data['air_quality'], str) and data['air_quality'].upper() == 'NAN':
            data['air_quality'] = float('nan')
        else:
            raw_score = float(data['air_quality'])
            data['air_quality'] = convert_air_quality_to_percent(raw_score)
        
        # These fields must not be NaN
        data['bme_iaq_accuracy'] = int(data['bme_iaq_accuracy'])
        data['station_id'] = int(data['station_id'])
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