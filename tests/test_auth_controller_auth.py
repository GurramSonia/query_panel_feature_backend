import pytest
from flask import Flask, session
from flask.testing import FlaskClient

from src.controller.auth.auth_controller_auth import auth_ns_auth
from src.controller import API
from src.controller import queryapi 

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret'
    #API.init_app(app)
    app.register_blueprint(queryapi) 
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_encryption_token(client):
    response = client.get('/queryapi/auth/get-encryption-token')
    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert len(data['token']) == 32  # 16 bytes hex

def test_current_user_unauthorized(client):
    response = client.get('/queryapi/auth/current_user')
    assert response.status_code == 401
    assert response.get_json()['error'] == "Unauthorized"

def test_query_login_invalid_json(client):
    response = client.post('/queryapi/auth/query-login', data="notjson", content_type='application/json')
    assert response.status_code == 400 or response.status_code == 500

def test_query_signup_success(monkeypatch, client):
    # Patch signup_user_service to return a dummy response
    monkeypatch.setattr(
        "src.service.auth_service.signup_user_service",
        lambda data: ({"message": "Signup successful"}, 201)
    )
    payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password1!",
        "iv": "1234567812345678",
        "token": "sometoken",
        "role": "user"
    }
    response = client.post('/queryapi/auth/query-signup', json=payload)
    assert response.status_code == 201
    assert "Signup successful" in response.get_json()["message"]

def test_query_login_success(monkeypatch, client):
    # Patch login_user_service to return a dummy response
    monkeypatch.setattr(
        "src.service.auth_service.login_user_service",
        lambda data: ({"message": "Login successful", "jwtToken": "token"}, 200)
    )
    payload = {
        "username": "testuser",
        "password": "Password1!",
        "iv": "1234567812345678",
        "token": "sometoken"
    }
    response = client.post('/queryapi/auth/query-login', json=payload)
    assert response.status_code == 200
    assert "Login successful" in response.get_json()["message"]