from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.models import db, User
from app.schemas import LoginRequest, UserCreate, UserResponse, LoginResponse
from app.utils.logger import log_request, log_error

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            user_data = UserCreate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Check if user exists
        if User.query.filter_by(username=user_data.username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=user_data.email).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            role=user_data.role
        )
        new_user.set_password(user_data.password)
        
        db.session.add(new_user)
        db.session.commit()
        
        log_request(user_id=new_user.id, action='user_registered', status_code=201)
        
        return jsonify({
            'message': 'User created successfully',
            'user': UserResponse(**new_user.to_dict()).dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error('Registration failed', e)
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            login_data = LoginRequest(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Find user
        user = User.query.filter_by(username=login_data.username).first()
        
        if not user or not user.check_password(login_data.password):
            log_request(action='login_failed', details={'username': login_data.username}, status_code=401)
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create token
        access_token = create_access_token(identity=user.id)
        
        log_request(user_id=user.id, action='user_logged_in', status_code=200)
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': UserResponse(**user.to_dict()).dict()
        }), 200
        
    except Exception as e:
        log_error('Login failed', e)
        return jsonify({'error': 'Internal server error'}), 500
