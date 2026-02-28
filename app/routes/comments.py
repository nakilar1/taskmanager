from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.models import db, Comment, Task, TaskAssignment, Project
from app.schemas import CommentCreate, CommentUpdate, CommentResponse
from app.utils.logger import log_request, log_error

comments_bp = Blueprint('comments', __name__, url_prefix='/api/comments')

@comments_bp.route('', methods=['GET'])
@jwt_required()
def get_comments():
    """Get comments for a task"""
    try:
        current_user_id = get_jwt_identity()
        
        task_id = request.args.get('task_id', type=int)
        if not task_id:
            return jsonify({'error': 'task_id query parameter is required'}), 400
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.desc()).all()
        result = [CommentResponse(**comment.to_dict()).dict() for comment in comments]
        
        log_request(user_id=current_user_id, action=f'listed_comments_for_task_{task_id}', status_code=200)
        
        return jsonify({'comments': result}), 200
        
    except Exception as e:
        log_error('Failed to get comments', e)
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/<int:comment_id>', methods=['GET'])
@jwt_required()
def get_comment(comment_id):
    """Get comment by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        log_request(user_id=current_user_id, action=f'viewed_comment_{comment_id}', status_code=200)
        
        return jsonify(CommentResponse(**comment.to_dict()).dict()), 200
        
    except Exception as e:
        log_error(f'Failed to get comment {comment_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('', methods=['POST'])
@jwt_required()
def create_comment():
    """Create new comment"""
    try:
        current_user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            comment_data = CommentCreate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Check if task exists
        task = Task.query.get(comment_data.task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Create comment
        new_comment = Comment(
            text=comment_data.text,
            task_id=comment_data.task_id,
            author_id=current_user_id
        )
        
        db.session.add(new_comment)
        db.session.commit()
        
        log_request(user_id=current_user_id, action='created_comment', details={'comment_id': new_comment.id}, status_code=201)
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': CommentResponse(**new_comment.to_dict()).dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error('Failed to create comment', e)
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    """Update comment"""
    try:
        current_user_id = get_jwt_identity()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Only author can update
        if comment.author_id != current_user_id:
            return jsonify({'error': 'Access denied - only author can update'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            update_data = CommentUpdate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Update fields
        comment.text = update_data.text
        
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'updated_comment_{comment_id}', status_code=200)
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': CommentResponse(**comment.to_dict()).dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to update comment {comment_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete comment"""
    try:
        current_user_id = get_jwt_identity()
        from app.models import User
        current_user = User.query.get(current_user_id)
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        # Only author or admin can delete
        if comment.author_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied - only author or admin can delete'}), 403
        
        db.session.delete(comment)
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'deleted_comment_{comment_id}', status_code=200)
        
        return jsonify({'message': 'Comment deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to delete comment {comment_id}', e)
        return jsonify({'error': 'Internal server error'}), 500
