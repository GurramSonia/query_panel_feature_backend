import os
import pytest
from flask import Flask
import settings 

# Patch environment variables for testing
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['JWT_SECRET'] = 'test_jwt_secret'

# Import after patching env vars
from src.controller import init_app, queryapi

def test_init_app_configures_app(monkeypatch):
    # Patch settings variables used in init_app
    monkeypatch.setattr(settings, "MYSQL_USER", "testuser")
    monkeypatch.setattr(settings, "MYSQL_PASSWORD", "testpass")
    monkeypatch.setattr(settings, "MYSQL_HOST", "localhost")
    monkeypatch.setattr(settings, "MYSQL_PORT", "3306")
    monkeypatch.setattr(settings, "MYSQL_DATABASE", "testdb")
    monkeypatch.setattr(settings, "MYSQL_LOCAL_USER_PASS", "localpass")
    monkeypatch.setattr(settings, "MONGO_USERNAME", "mongouser")
    monkeypatch.setattr(settings, "MONGO_PASSWORD", "mongopass")
    monkeypatch.setattr(settings, "MONGO_HOST", "localhost")
    monkeypatch.setattr(settings, "MONGO_PORT", "27017")
    monkeypatch.setattr(settings, "MONGO_DATABASE", "mongotestdb")
    monkeypatch.setattr(settings, "JWT_SECRET", "test_jwt_secret")

    app = Flask(__name__)
    init_app(app)

    # Check config values
    app.config['WTF_CSRF_ENABLED'] = False
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith('mysql+pymysql://')
    assert app.config['MONGO_URI'].startswith('mongodb://')
    assert app.config['SECRET_KEY'] == 'test_secret'
    assert app.config['JWT_SECRET'] == 'test_jwt_secret'

    # Check blueprint registration
    assert 'my_blueprint' in app.blueprints

    # Check that the API object is attached to the blueprint
    assert hasattr(queryapi, 'name')