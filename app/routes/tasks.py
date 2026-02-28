from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.models import db, Task, Project, User, TaskAssignment
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, AssignmentCreate, AssignmentResponse
from app.utils.logger import log_request, log_error

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters for filtering
        project_id = request.args.get('project_id', type=int)
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        # Get tasks where user is assigned or owner of project
        query = Task.query.join(Project).filter(
            (Project.owner_id == current_user_id) | 
            (Task.id.in_(
                db.session.query(TaskAssignment.task_id).filter_by(user_id=current_user_id)
            ))
        )
        
        # Apply filters
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        
        tasks = query.all()
        result = [TaskResponse(**task.to_dict()).dict() for task in tasks]
        
        log_request(user_id=current_user_id, action='listed_tasks', status_code=200)
        
        return jsonify({'tasks': result}), 200
        
    except Exception as e:
        log_error('Failed to get tasks', e)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get task by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        log_request(user_id=current_user_id, action=f'viewed_task_{task_id}', status_code=200)
        
        return jsonify(TaskResponse(**task.to_dict()).dict()), 200
        
    except Exception as e:
        log_error(f'Failed to get task {task_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """Create new task"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            task_data = TaskCreate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Check if project exists and user has access
        project = Project.query.get(task_data.project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if project.owner_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied - only project owner can create tasks'}), 403
        
        # Create task
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            project_id=task_data.project_id
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        log_request(user_id=current_user_id, action='created_task', details={'task_id': new_task.id}, status_code=201)
        
        return jsonify({
            'message': 'Task created successfully',
            'task': TaskResponse(**new_task.to_dict()).dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error('Failed to create task', e)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update task"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check access - project owner, admin, or assigned user
        project = Project.query.get(task.project_id)
        is_assigned = TaskAssignment.query.filter_by(task_id=task_id, user_id=current_user_id).first() is not None
        
        if project.owner_id != current_user_id and current_user.role != 'admin' and not is_assigned:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate with Pydantic
        try:
            update_data = TaskUpdate(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = []
            for error in errors:
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_messages.append(f"{field}: {msg}")
            return jsonify({'error': 'Validation failed', 'details': error_messages}), 400
        
        # Update fields
        if update_data.title is not None:
            task.title = update_data.title
        if update_data.description is not None:
            task.description = update_data.description
        if update_data.status is not None:
            task.status = update_data.status
        if update_data.priority is not None:
            task.priority = update_data.priority
        
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'updated_task_{task_id}', status_code=200)
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': TaskResponse(**task.to_dict()).dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to update task {task_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete task"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Only project owner or admin can delete
        project = Project.query.get(task.project_id)
        if project.owner_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied - only project owner or admin can delete'}), 403
        
        db.session.delete(task)
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'deleted_task_{task_id}', status_code=200)
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to delete task {task_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

# Assignment endpoints
@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_task(task_id):
    """Assign user to task"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Only project owner or admin can assign
        project = Project.query.get(task.project_id)
        if project.owner_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied - only project owner can assign tasks'}), 403
        
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required'}), 400
        
        user_id = data['user_id']
        
        # Check if user exists
        user_to_assign = User.query.get(user_id)
        if not user_to_assign:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already assigned
        existing = TaskAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        if existing:
            return jsonify({'error': 'User already assigned to this task'}), 409
        
        # Create assignment
        assignment = TaskAssignment(task_id=task_id, user_id=user_id)
        db.session.add(assignment)
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'assigned_task_{task_id}_to_user_{user_id}', status_code=201)
        
        return jsonify({
            'message': 'User assigned to task successfully',
            'assignment': AssignmentResponse(**assignment.to_dict()).dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to assign task {task_id}', e)
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<int:task_id>/assign/<int:user_id>', methods=['DELETE'])
@jwt_required()
def unassign_task(task_id, user_id):
    """Remove user assignment from task"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Only project owner or admin can unassign
        project = Project.query.get(task.project_id)
        if project.owner_id != current_user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        assignment = TaskAssignment.query.filter_by(task_id=task_id, user_id=user_id).first()
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        db.session.delete(assignment)
        db.session.commit()
        
        log_request(user_id=current_user_id, action=f'unassigned_task_{task_id}_from_user_{user_id}', status_code=200)
        
        return jsonify({'message': 'User unassigned from task successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        log_error(f'Failed to unassign task {task_id}', e)
        return jsonify({'error': 'Internal server error'}), 500
