from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.models import db, Project, User
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.utils.logger import log_request, log_error

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

@projects_bp.route('', methods=['GET'])
@jwt_required()
def get_projects():
    """Get all projects for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's own projects and projects where they are assigned
        from app.models import Task, TaskAssignment
        
        owned_projects = Project.query.filter_by(owner_id=current_user_id).all()
        
        # Get projects where user is assigned to tasks
        assigned_task_ids = db.session.query(TaskAssignment.task_id).filter_by(user_id=current_user_id).subquery()
        assigned_tasks = Task.query.filter(Task.id.in_(assigned_task_ids)).all()
        assigned_project_ids = list(set([task.project_id for task in assigned_tasks]))
        assigned_projects = Project.query.filter(Project.id.in_(assigned_project_ids)).all()
        
        # Combine and deduplicate
        all_projects = list({p.id: p for p in owned_projects + assigned_projects}.values())
        result = [ProjectResponse(**project.to_dict()).dict() for project in all_projects]
        
        log_request(user_id=current_user_id, action='listed_projects', status_code=200)
        
        return jsonify({'projects': result}), 200
        
    except Exception as e:
        log_error('Failed to get projects', e)
        return jsonify({'error': 'Internal server error'}), 500

@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get project by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        log_request(user_id=current_user_id, action=f'viewed_project_{project_id}', status_code=200)
        
        return jsonify(ProjectResponse(**project.to_dict()).dict()), 200
        
    except Exception as e:
        log_error(f'Failed to get project {project_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """Create new project"""
    try:
        current_user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            project_data = ProjectCreate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Create project
        new_project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=current_user_id
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        log_request(user_id=current_user_id, action='created_project', details={'project_id': new_project.id}, status_code=201)
        
        return jsonify({
            'message': 'Project created successfully',
            'project': ProjectResponse(**new_project.to_dict()).dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error('Failed to create project', e)
        return jsonify({'error': 'Internal server error'}), 500

@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update project"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Only owner or admin can update
        if project.owner_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied - only owner or admin can update'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            update_data = ProjectUpdate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Update fields
        if update_data.name is not None:
            project.name = update_data.name
        if update_data.description is not None:
            project.description = update_data.description
        
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'updated_project_{project_id}', status_code=200)
        
        return jsonify({
            'message': 'Project updated successfully',
            'project': ProjectResponse(**project.to_dict()).dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to update project {project_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete project"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Only owner or admin can delete
        if project.owner_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied - only owner or admin can delete'}), 403
        
        db.session.delete(project)
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'deleted_project_{project_id}', status_code=200)
        
        return jsonify({'message': 'Project deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to delete project {project_id}', e)
        return jsonify({'error': 'Internal server error'}), 500
