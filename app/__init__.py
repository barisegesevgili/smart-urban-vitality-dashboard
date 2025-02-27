from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_apispec import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from .models.sensor_data import db, SensorData
from .utils.errors import register_error_handlers

def load_config():
    """Load configuration from environment variables in production, fall back to config.py in development"""
    current_env = os.environ.get('FLASK_ENV', 'development')
    
    if current_env == 'development':
        try:
            # First try to load from config.py
            from config import (
                FLASK_ENV, 
                DEBUG, 
                GOOGLE_MAPS_API_KEY,
                GOOGLE_MAPS_MAP_ID,
                STATIONS, 
                THRESHOLDS,
                UPDATE_INTERVALS
            )
            return {
                'FLASK_ENV': FLASK_ENV,
                'DEBUG': DEBUG,
                'GOOGLE_MAPS_API_KEY': GOOGLE_MAPS_API_KEY,
                'GOOGLE_MAPS_MAP_ID': GOOGLE_MAPS_MAP_ID,
                'STATIONS': STATIONS,
                'THRESHOLDS': THRESHOLDS,
                'UPDATE_INTERVALS': UPDATE_INTERVALS
            }
        except ImportError:
            try:
                # If config.py is not found, try environment variables
                stations_str = os.environ.get('STATIONS', '{}')
                thresholds_str = os.environ.get('THRESHOLDS', '{}')
                update_intervals_str = os.environ.get('UPDATE_INTERVALS', '{}')
                maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
                maps_id = os.environ.get('GOOGLE_MAPS_MAP_ID')
                
                # Parse JSON strings, ensuring string keys for stations
                stations_dict = json.loads(stations_str)
                stations = {str(k): v for k, v in stations_dict.items()}
                
                return {
                    'FLASK_ENV': current_env,
                    'DEBUG': os.environ.get('DEBUG', 'true').lower() == 'true',
                    'GOOGLE_MAPS_API_KEY': maps_key,
                    'GOOGLE_MAPS_MAP_ID': maps_id,
                    'STATIONS': stations,
                    'THRESHOLDS': json.loads(thresholds_str),
                    'UPDATE_INTERVALS': json.loads(update_intervals_str)
                }
            except json.JSONDecodeError:
                return default_config()
    else:  # production mode
        try:
            stations_str = os.environ.get('STATIONS', '{}')
            thresholds_str = os.environ.get('THRESHOLDS', '{}')
            update_intervals_str = os.environ.get('UPDATE_INTERVALS', '{}')
            maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            maps_id = os.environ.get('GOOGLE_MAPS_MAP_ID')
            
            # Parse JSON strings, ensuring string keys for stations
            stations_dict = json.loads(stations_str)
            stations = {str(k): v for k, v in stations_dict.items()}
            
            return {
                'FLASK_ENV': current_env,
                'DEBUG': os.environ.get('DEBUG', 'false').lower() == 'true',
                'GOOGLE_MAPS_API_KEY': maps_key,
                'GOOGLE_MAPS_MAP_ID': maps_id,
                'STATIONS': stations,
                'THRESHOLDS': json.loads(thresholds_str),
                'UPDATE_INTERVALS': json.loads(update_intervals_str)
            }
        except json.JSONDecodeError:
            return default_config()

def default_config():
    return {
        'FLASK_ENV': 'production',
        'DEBUG': False,
        'GOOGLE_MAPS_API_KEY': '',
        'GOOGLE_MAPS_MAP_ID': '',
        'STATIONS': {
            "1": {"name": "Garching/IOT-Lab", "location": {"lat": 48.26264036847362, "lng": 11.668331022751858}},
            "2": {"name": "Garching/Basketball Court", "location": {"lat": 48.26364466819253, "lng": 11.668459013506432}},
            "3": {"name": "Garching/IOT-Lab Balcony", "location": {"lat": 48.26271268490997, "lng": 11.66840813626192}}
        },
        'THRESHOLDS': {},
        'UPDATE_INTERVALS': {'charts': 30000, 'alerts': 30000}
    }

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["10000 per day", "1000 per hour"],
        storage_uri="memory://"
    )
    app.limiter = limiter  # Store limiter instance on app

    # Register error handlers
    register_error_handlers(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/smart_urban_vitality.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Smart Urban Vitality startup')

    # Load configuration
    config = load_config()
    app.config.update(config)

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # API documentation configuration
    app.config.update({
        'APISPEC_SPEC': APISpec(
            title='Smart Urban Vitality API',
            version='v1',
            plugins=[MarshmallowPlugin()],
            openapi_version='2.0.0'
        ),
        'APISPEC_SWAGGER_URL': '/swagger/',  # URI to access API Doc JSON
        'APISPEC_SWAGGER_UI_URL': '/swagger-ui/'  # URI to access UI of API Doc
    })

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    docs = FlaskApiSpec(app)

    # Create tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('Database tables created successfully')
        except Exception as e:
            app.logger.error(f'Error creating database tables: {str(e)}')

    # Register routes
    from .routes import register_routes
    register_routes(app)

    # Register all documented endpoints with API documentation
    with app.app_context():
        for view in app.view_functions.values():
            if hasattr(view, '_spec'):
                docs.register(view)

    return app
