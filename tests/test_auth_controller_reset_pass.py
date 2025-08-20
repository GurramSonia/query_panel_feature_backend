import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

from src.controller.auth.auth_controller_reset_pass import auth_ns_reset_pass
from src.controller import API, queryapi

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret'
    API.init_app(app)
    app.register_blueprint(queryapi) 
    return app
    #app.register_blueprint(auth_ns_reset_pass)
    #return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch("src.util.auth_utils_reset_pass.check_user_existence_by_email")
@patch("src.util.auth_utils_reset_pass.generate_reset_token", return_value="testtoken")
@patch("smtplib.SMTP")
def test_forgot_password_success(mock_smtp, mock_generate_token, mock_check_user, client):
    mock_check_user.return_value = MagicMock(email="test@example.com")
    payload = {"email": "test@example.com"}
    response = client.post("/queryapi/auth/forgot-password", json=payload)
    assert response.status_code == 200
    assert "Password reset link sent" in response.get_json()["message"]

@patch("src.util.auth_utils_reset_pass.check_user_existence_by_email", return_value=None)
def test_forgot_password_email_not_found(mock_check_user, client):
    payload = {"email": "notfound@example.com"}
    response = client.post("/queryapi/auth/forgot-password", json=payload)
    assert response.status_code == 404
    assert "Email not found" in response.get_json()["error"]

@patch("src.util.auth_utils_reset_pass.get_user_by_token", return_value=MagicMock(id=1, username="testuser"))
@patch("src.util.auth_utils_reset_pass.reset_user_password", return_value=None)
@patch("werkzeug.security.generate_password_hash", return_value="hashedpass")
def test_reset_password_success(mock_hash, mock_reset_user, mock_get_user, client):
    payload = {"token": "testtoken", "newPassword": "Password1!"}
    response = client.post("/queryapi/auth/reset-password", json=payload)
    assert response.status_code == 200
    assert "Password reset successfully" in response.get_json()["message"]

@patch("src.util.auth_utils_reset_pass.get_user_by_token", return_value=None)
def test_reset_password_invalid_token(mock_get_user, client):
    payload = {"token": "badtoken", "newPassword": "Password1!"}
    response = client.post("/queryapi/auth/reset-password", json=payload)
    assert response.status_code == 400
    assert "Invalid or expired token" in response.get_json()["error"]

def test_reset_password_missing_fields(client):
    payload = {"token": "", "newPassword": ""}
    response = client.post("/queryapi/auth/reset-password", json=payload)
    assert response.status_code == 400
    assert "Token and new password are required" in response.get_json()["error"]