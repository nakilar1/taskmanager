import pytest
from app import create_app, db
from app.models import User, Project, Task, TaskAssignment, Comment

@pytest.fixture
def app():
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Create a user and get token
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }
    
    # Register user
    client.post('/api/auth/register', json=user_data)
    
    # Login to get token
    login_response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    token = login_response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def test_user(client):
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }
    client.post('/api/auth/register', json=user_data)
    return user_data

@pytest.fixture
def test_project(client, auth_headers):
    project_data = {
        'name': 'Test Project',
        'description': 'A test project'
    }
    response = client.post('/api/projects', json=project_data, headers=auth_headers)
    return response.json['project']

@pytest.fixture
def test_task(client, auth_headers, test_project):
    task_data = {
        'title': 'Test Task',
        'description': 'A test task',
        'status': 'todo',
        'priority': 'medium',
        'project_id': test_project['id']
    }
    response = client.post('/api/tasks', json=task_data, headers=auth_headers)
    return response.json['task']
