from flask import jsonify
from werkzeug.exceptions import HTTPException

class APIError(Exception):
    """Base exception for API errors"""
    status_code = 500
    message = "Internal server error"

    def __init__(self, message=None, status_code=None):
        super().__init__()
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        return {'error': self.message}

class ValidationError(APIError):
    status_code = 400
    message = "Validation error"

class ResourceNotFoundError(APIError):
    status_code = 404
    message = "Resource not found"

class RateLimitError(APIError):
    status_code = 429
    message = "Too many requests"

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify({'error': str(error.message)})
        response.status_code = error.status_code
        return response

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        response = jsonify({'error': error.description})
        response.status_code = error.code
        return response

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        if isinstance(error, ValidationError):
            return handle_validation_error(error)
        app.logger.error(f'Unhandled error: {str(error)}')
        response = jsonify({'error': str(error)})
        response.status_code = 500
        return response 