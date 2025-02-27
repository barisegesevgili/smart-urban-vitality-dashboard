from marshmallow import Schema, fields

class SensorDataSchema(Schema):
    """Schema for sensor data validation and serialization."""
    id = fields.Int(dump_only=True)
    timestamp = fields.DateTime(required=True)
    temperature = fields.Float(required=True)
    humidity = fields.Float(required=True)
    uv_index = fields.Float(required=True)
    air_quality = fields.Float(required=True)
    co2e = fields.Float(required=True)
    fill_level = fields.Float(required=True)
    rtc_time = fields.DateTime(required=True)
    bme_iaq_accuracy = fields.Int(required=True)
    station_id = fields.Int(required=True)

class ErrorSchema(Schema):
    """Schema for error responses."""
    error = fields.Str(required=True)

class SuccessSchema(Schema):
    """Schema for success responses."""
    message = fields.Str(required=True)

# Response schemas
sensor_data_response = {
    200: {'schema': SensorDataSchema(many=True)},
    400: {'schema': ErrorSchema},
    500: {'schema': ErrorSchema}
}

success_response = {
    201: {'schema': SuccessSchema},
    400: {'schema': ErrorSchema},
    500: {'schema': ErrorSchema}
} 