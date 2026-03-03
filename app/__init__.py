from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.models import db
from app.config import config
from app.utils.logger import setup_logging
import os

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5001", "http://127.0.0.1:5001"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type"]
        }
    })
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    
    # Setup logging
    setup_logging(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token required'}), 401
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'Task Manager API'}), 200
    
    # Serve frontend
    @app.route('/', methods=['GET'])
    def serve_frontend():
        return send_from_directory('static', 'index.html')
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.projects import projects_bp
    from app.routes.tasks import tasks_bp
    from app.routes.comments import comments_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(comments_bp)
    
    return app
