import pytest
import json

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

class TestAuth:
    """Test authentication endpoints"""
    
    def test_register_user_success(self, client):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 201
        assert 'access_token' not in response.json  # Register doesn't return token
        assert response.json['user']['username'] == 'newuser'
        assert response.json['user']['email'] == 'newuser@example.com'
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        data = {
            'username': 'testuser',
            'email': 'different@example.com',
            'password': 'password123'
        }
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 409
        assert 'error' in response.json
    
    def test_register_invalid_data(self, client):
        """Test registration with invalid data"""
        data = {
            'username': 'ab',  # Too short
            'email': 'invalid-email',
            'password': '123'  # Too short
        }
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'details' in response.json
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 200
        assert 'access_token' in response.json
        assert response.json['token_type'] == 'Bearer'
        assert response.json['user']['username'] == 'testuser'
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 401
        assert 'error' in response.json
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        response = client.post('/api/auth/login', json=data)
        
        assert response.status_code == 401
        assert 'error' in response.json

class TestUsers:
    """Test user endpoints"""
    
    def test_get_users_without_token(self, client):
        """Test getting users without authentication"""
        response = client.get('/api/users')
        
        assert response.status_code == 401
        assert 'error' in response.json
    
    def test_get_users_with_token(self, client, auth_headers):
        """Test getting users with authentication"""
        response = client.get('/api/users', headers=auth_headers)
        
        # Should work but may return empty list for non-admin
        assert response.status_code in [200, 403]
    
    def test_get_user_by_id(self, client, auth_headers):
        """Test getting user by ID"""
        # First get current user info from login
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        user_id = login_response.json['user']['id']
        
        response = client.get(f'/api/users/{user_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['username'] == 'testuser'
    
    def test_update_user(self, client, auth_headers):
        """Test updating user"""
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        user_id = login_response.json['user']['id']
        
        data = {
            'username': 'updateduser'
        }
        response = client.put(f'/api/users/{user_id}', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['user']['username'] == 'updateduser'
    
    def test_delete_user(self, client, auth_headers):
        """Test deleting user"""
        # Create a new user to delete
        new_user_data = {
            'username': 'todelete',
            'email': 'delete@example.com',
            'password': 'password123'
        }
        client.post('/api/auth/register', json=new_user_data)
        
        login_response = client.post('/api/auth/login', json={
            'username': 'todelete',
            'password': 'password123'
        })
        user_id = login_response.json['user']['id']
        token = login_response.json['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        response = client.delete(f'/api/users/{user_id}', headers=headers)
        
        assert response.status_code == 200
        assert 'message' in response.json

class TestProjects:
    """Test project CRUD operations"""
    
    def test_create_project(self, client, auth_headers):
        """Test creating a project"""
        data = {
            'name': 'New Project',
            'description': 'Project description'
        }
        response = client.post('/api/projects', json=data, headers=auth_headers)
        
        assert response.status_code == 201
        assert response.json['project']['name'] == 'New Project'
        assert response.json['project']['description'] == 'Project description'
    
    def test_create_project_invalid_data(self, client, auth_headers):
        """Test creating project with invalid data"""
        data = {
            'name': '',  # Empty name
            'description': 'Description'
        }
        response = client.post('/api/projects', json=data, headers=auth_headers)
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_get_projects(self, client, auth_headers, test_project):
        """Test getting projects"""
        response = client.get('/api/projects', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'projects' in response.json
        assert len(response.json['projects']) >= 1
    
    def test_get_project_by_id(self, client, auth_headers, test_project):
        """Test getting project by ID"""
        project_id = test_project['id']
        response = client.get(f'/api/projects/{project_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['id'] == project_id
    
    def test_get_nonexistent_project(self, client, auth_headers):
        """Test getting non-existent project"""
        response = client.get('/api/projects/999999', headers=auth_headers)
        
        assert response.status_code == 404
        assert 'error' in response.json
    
    def test_update_project(self, client, auth_headers, test_project):
        """Test updating project"""
        project_id = test_project['id']
        data = {
            'name': 'Updated Project Name'
        }
        response = client.put(f'/api/projects/{project_id}', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['project']['name'] == 'Updated Project Name'
    
    def test_delete_project(self, client, auth_headers, test_project):
        """Test deleting project"""
        project_id = test_project['id']
        response = client.delete(f'/api/projects/{project_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'message' in response.json

class TestTasks:
    """Test task CRUD operations"""
    
    def test_create_task(self, client, auth_headers, test_project):
        """Test creating a task"""
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'status': 'todo',
            'priority': 'high',
            'project_id': test_project['id']
        }
        response = client.post('/api/tasks', json=data, headers=auth_headers)
        
        assert response.status_code == 201
        assert response.json['task']['title'] == 'New Task'
        assert response.json['task']['status'] == 'todo'
    
    def test_create_task_invalid_status(self, client, auth_headers, test_project):
        """Test creating task with invalid status"""
        data = {
            'title': 'New Task',
            'project_id': test_project['id'],
            'status': 'invalid_status'
        }
        response = client.post('/api/tasks', json=data, headers=auth_headers)
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_get_tasks(self, client, auth_headers, test_task):
        """Test getting tasks"""
        response = client.get('/api/tasks', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'tasks' in response.json
    
    def test_get_task_by_id(self, client, auth_headers, test_task):
        """Test getting task by ID"""
        task_id = test_task['id']
        response = client.get(f'/api/tasks/{task_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['id'] == task_id
    
    def test_update_task(self, client, auth_headers, test_task):
        """Test updating task"""
        task_id = test_task['id']
        data = {
            'title': 'Updated Task Title',
            'status': 'in_progress'
        }
        response = client.put(f'/api/tasks/{task_id}', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['task']['title'] == 'Updated Task Title'
        assert response.json['task']['status'] == 'in_progress'
    
    def test_delete_task(self, client, auth_headers, test_task):
        """Test deleting task"""
        task_id = test_task['id']
        response = client.delete(f'/api/tasks/{task_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'message' in response.json

class TestComments:
    """Test comment operations"""
    
    def test_create_comment(self, client, auth_headers, test_task):
        """Test creating a comment"""
        data = {
            'text': 'This is a test comment',
            'task_id': test_task['id']
        }
        response = client.post('/api/comments', json=data, headers=auth_headers)
        
        assert response.status_code == 201
        assert response.json['comment']['text'] == 'This is a test comment'
    
    def test_get_comments(self, client, auth_headers, test_task):
        """Test getting comments for a task"""
        # First create a comment
        comment_data = {
            'text': 'Test comment',
            'task_id': test_task['id']
        }
        client.post('/api/comments', json=comment_data, headers=auth_headers)
        
        # Get comments
        response = client.get(f'/api/comments?task_id={test_task["id"]}', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'comments' in response.json
    
    def test_update_comment(self, client, auth_headers, test_task):
        """Test updating comment"""
        # Create comment first
        comment_data = {
            'text': 'Original comment',
            'task_id': test_task['id']
        }
        create_response = client.post('/api/comments', json=comment_data, headers=auth_headers)
        comment_id = create_response.json['comment']['id']
        
        # Update comment
        data = {
            'text': 'Updated comment text'
        }
        response = client.put(f'/api/comments/{comment_id}', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json['comment']['text'] == 'Updated comment text'
    
    def test_delete_comment(self, client, auth_headers, test_task):
        """Test deleting comment"""
        # Create comment first
        comment_data = {
            'text': 'Comment to delete',
            'task_id': test_task['id']
        }
        create_response = client.post('/api/comments', json=comment_data, headers=auth_headers)
        comment_id = create_response.json['comment']['id']
        
        # Delete comment
        response = client.delete(f'/api/comments/{comment_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'message' in response.json

class TestAssignments:
    """Test task assignment operations"""
    
    def test_assign_user_to_task(self, client, auth_headers, test_task):
        """Test assigning user to task"""
        # First create another user
        user_data = {
            'username': 'assignee',
            'email': 'assignee@example.com',
            'password': 'password123'
        }
        client.post('/api/auth/register', json=user_data)
        
        # Get the user id
        login_response = client.post('/api/auth/login', json=user_data)
        user_id = login_response.json['user']['id']
        
        # Assign user to task
        data = {
            'user_id': user_id
        }
        response = client.post(f'/api/tasks/{test_task["id"]}/assign', json=data, headers=auth_headers)
        
        assert response.status_code == 201
        assert 'assignment' in response.json
    
    def test_unassign_user_from_task(self, client, auth_headers, test_task):
        """Test unassigning user from task"""
        # First create and assign user
        user_data = {
            'username': 'to_unassign',
            'email': 'tounassign@example.com',
            'password': 'password123'
        }
        client.post('/api/auth/register', json=user_data)
        
        login_response = client.post('/api/auth/login', json=user_data)
        user_id = login_response.json['user']['id']
        
        # Assign
        client.post(f'/api/tasks/{test_task["id"]}/assign', json={'user_id': user_id}, headers=auth_headers)
        
        # Unassign
        response = client.delete(f'/api/tasks/{test_task["id"]}/assign/{user_id}', headers=auth_headers)
        
        assert response.status_code == 200
        assert 'message' in response.json

class TestAccessControl:
    """Test access control and authorization"""
    
    def test_access_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/users')
        
        assert response.status_code == 401
        assert 'error' in response.json
    
    def test_access_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/api/users', headers=headers)
        
        assert response.status_code == 401
        assert 'error' in response.json
