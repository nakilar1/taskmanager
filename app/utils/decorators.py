from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User
from app.utils.logger import log_error

def jwt_required_custom(fn):
    """Custom JWT required decorator with better error handling"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            log_error("JWT verification failed", e)
            return jsonify({'error': 'Unauthorized - valid token required'}), 401
    return wrapper

def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            log_error("Admin check failed", e)
            return jsonify({'error': 'Unauthorized'}), 401
    return wrapper
