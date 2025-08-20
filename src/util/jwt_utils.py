import jwt
from flask import request, current_app
from functools import wraps
from datetime import datetime, timedelta, timezone

def generate_jwt_token(user_id, role, username):
    payload = {
        'user_id': user_id,
        'role': role,
        'username': username,
        #'exp': datetime.utcnow() + timedelta(minutes=10)
        'exp': datetime.now(timezone.utc) + timedelta(minutes=2)
    }
    secret = current_app.config.get('JWT_SECRET', 'your_jwt_secret')
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return {"error": "Missing or invalid Authorization header"}, 401
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, current_app.config.get('JWT_SECRET', 'your_jwt_secret'), algorithms=['HS256'])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401
        return f(*args, **kwargs)
    return decorated
