import os
from app import create_app, db
from app.models import User, Project, Task, TaskAssignment, Comment

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Project': Project,
        'Task': Task,
        'TaskAssignment': TaskAssignment,
        'Comment': Comment
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
