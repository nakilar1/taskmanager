import logging
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User

def setup_logging(app):
    log_file = app.config.get('LOG_FILE', 'app.log')
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(getattr(logging, log_level))

def log_request(user_id=None, action=None, details=None, status_code=None):
    """Log user actions"""
    from flask import current_app
    timestamp = datetime.utcnow().isoformat()
    ip_address = request.remote_addr if request else 'unknown'
    method = request.method if request else 'unknown'
    endpoint = request.endpoint if request else 'unknown'
    
    log_entry = {
        'timestamp': timestamp,
        'user_id': user_id,
        'action': action or f"{method} {endpoint}",
        'details': details,
        'ip_address': ip_address,
        'status_code': status_code
    }
    
    current_app.logger.info(f"ACTION: {log_entry}")

def log_error(error_message, exception=None):
    """Log errors"""
    from flask import current_app
    timestamp = datetime.utcnow().isoformat()
    
    error_entry = {
        'timestamp': timestamp,
        'error': error_message,
        'exception': str(exception) if exception else None
    }
    
    current_app.logger.error(f"ERROR: {error_entry}")
