import os
import sys

# Add the project directory to the sys.path
path = '/home/yourusername/taskmanager'
if path not in sys.path:
    sys.path.insert(0, path)

from app import create_app

# Create application instance
application = create_app(os.getenv('FLASK_ENV', 'production'))
