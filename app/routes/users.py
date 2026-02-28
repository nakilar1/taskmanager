from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.models import db, User
from app.schemas import UserCreate, UserUpdate, UserResponse
from app.utils.decorators import admin_required
from app.utils.logger import log_request, log_error

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        users = User.query.all()
        result = [UserResponse(**user.to_dict()).dict() for user in users]
        
        log_request(user_id=current_user_id, action='listed_all_users', status_code=200)
        
        return jsonify({'users': result}), 200
        
    except Exception as e:
        log_error('Failed to get users', e)
        return jsonify({'error': 'Internal server error'}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user by ID"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can only see their own profile or admins can see any
        if current_user_id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        log_request(user_id=current_user_id, action=f'viewed_user_{user_id}', status_code=200)
        
        return jsonify(UserResponse(**user.to_dict()).dict()), 200
        
    except Exception as e:
        log_error(f'Failed to get user {user_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can only update their own profile or admins can update any
        if current_user_id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            update_data = UserUpdate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Update fields
        if update_data.username:
            existing = User.query.filter_by(username=update_data.username).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Username already exists'}), 409
            user.username = update_data.username
        
        if update_data.email:
            existing = User.query.filter_by(email=update_data.email).first()
            if existing and existing.id != user_id:
                return jsonify({'error': 'Email already exists'}), 409
            user.email = update_data.email
        
        # Only admins can change roles
        if update_data.role and current_user.role == 'admin':
            user.role = update_data.role
        
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'updated_user_{user_id}', status_code=200)
        
        return jsonify({
            'message': 'User updated successfully',
            'user': UserResponse(**user.to_dict()).dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to update user {user_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete user (admin only or self)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can delete themselves or admins can delete any
        if current_user_id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'deleted_user_{user_id}', status_code=200)
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to delete user {user_id}', e)
        return jsonify({'error': 'Internal server error'}), 500
