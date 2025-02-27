import pytest
from app import create_app
from app.models.sensor_data import db as _db

@pytest.fixture
def app():
    """Create application for the tests."""
    _app = create_app()
    _app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'DEBUG': False,
        'GOOGLE_MAPS_API_KEY': 'test_key',
        'GOOGLE_MAPS_MAP_ID': 'test_map_id',
        'STATIONS': {
            "1": {"name": "Test Station", "location": {"lat": 0, "lng": 0}}
        },
        'THRESHOLDS': {},
        'UPDATE_INTERVALS': {'charts': 30000, 'alerts': 30000}
    })
    return _app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def db(app):
    """Create database for the tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all() 