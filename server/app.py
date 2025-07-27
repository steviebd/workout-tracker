import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
from db import init_db
<<<<<<< HEAD
from auth import login, register, change_password, get_password_policy, get_current_user_id, require_admin, forgot_password, reset_password, get_current_user
from models import Template, TemplateExercise, Session, SessionExercise, User, PasswordResetToken
from email_service import email_service
from validation import (
    validate_request, validate_json_size, ValidationError,
    TEMPLATE_CREATION_SCHEMA, TEMPLATE_UPDATE_SCHEMA, SESSION_CREATION_SCHEMA,
    validate_username
)
from security_logger import log_data_access, log_access_denied, log_security_event
=======
from auth_authelia import authelia_required, get_current_user_id, get_user_info, admin_required
from models import Template, TemplateExercise, Session, SessionExercise, User
>>>>>>> 114797d (added authelia)

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = config[config_name]()  # Initialize config instance
    app.config.from_object(config_obj)
    
    # Configure static files (use absolute path)
    app.static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public'))
    
    # Initialize extensions
<<<<<<< HEAD
    jwt = JWTManager(app)
    
    # Configure rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=config_obj.RATE_LIMIT_DEFAULT.split(', '),
        storage_uri=config_obj.RATE_LIMIT_STORAGE_URI
    )
    
    # Configure CORS with security
    CORS(app, 
         origins=config_obj.CORS_ORIGINS,
         supports_credentials=config_obj.CORS_SUPPORTS_CREDENTIALS,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
=======
    CORS(app)
>>>>>>> 114797d (added authelia)
    
    # Initialize database
    init_db()
    
    # Register routes
    register_routes(app, limiter, config_obj)
    
    return app

<<<<<<< HEAD
def register_routes(app, limiter, config_obj):
    # Auth routes
    @app.route('/api/auth/login', methods=['POST'])
    @limiter.limit(config_obj.RATE_LIMIT_AUTH_LOGIN)
    def auth_login():
        return login()
    
    @app.route('/api/auth/register', methods=['POST'])
    @limiter.limit(config_obj.RATE_LIMIT_AUTH_REGISTER)
    @validate_json_size(10)  # Small limit for auth data
    def auth_register():
        return register()
    
    @app.route('/api/auth/change-password', methods=['PUT'])
    @jwt_required()
    @limiter.limit("10 per minute")  # Rate limit password changes
    @validate_json_size(10)
    def auth_change_password():
        return change_password()
    
    @app.route('/api/auth/password-policy', methods=['GET'])
    def auth_password_policy():
        return get_password_policy()
    
    @app.route('/api/auth/forgot-password', methods=['POST'])
    @limiter.limit("5 per minute")  # Rate limit password reset requests
    @validate_json_size(10)
    def auth_forgot_password():
        return forgot_password()
    
    @app.route('/api/auth/reset-password', methods=['POST'])
    @limiter.limit("10 per minute")
    @validate_json_size(10)
    def auth_reset_password():
        return reset_password()

    # Admin routes
    @app.route('/api/admin/users', methods=['GET'])
    @require_admin
    def admin_get_users():
        users = User.get_all_users()
        return jsonify(users)
    
    @app.route('/api/admin/users', methods=['POST'])
    @require_admin
    @validate_json_size(10)
    def admin_create_user():
        data = request.get_json()
        if not data or not all(k in data for k in ['username', 'email', 'password', 'role']):
            return jsonify({'error': 'Username, email, password, and role required'}), 400
        
        try:
            validate_username(data['username'])
            
            if data['role'] not in ['admin', 'user']:
                return jsonify({'error': 'Role must be admin or user'}), 400
            
            user_id = User.create(
                data['username'], 
                data['password'], 
                data['email'].lower().strip(), 
                data['role'],
                must_change_password=True
            )
            
            if user_id is None:
                return jsonify({'error': 'Username or email already exists'}), 409
            
            # Send email with credentials
            email_service.send_admin_created_user_email(
                data['email'], data['username'], data['password']
            )
            
            return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
    @require_admin
    @validate_json_size(10)
    def admin_update_user(user_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Prevent editing own role
        current_user = get_current_user()
        if current_user['id'] == user_id and 'role' in data:
            return jsonify({'error': 'Cannot change your own role'}), 400
        
        try:
            success, message = User.update_user(
                user_id,
                username=data.get('username'),
                email=data.get('email'),
                role=data.get('role')
            )
            
            if success:
                return jsonify({'message': message})
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            return jsonify({'error': 'Failed to update user'}), 500
    
    @app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
    @require_admin
    def admin_delete_user(user_id):
        # Prevent deleting own account
        current_user = get_current_user()
        if current_user['id'] == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        success = User.delete_user(user_id)
        if success:
            return '', 204
        else:
            return jsonify({'error': 'User not found'}), 404
    
    @app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
    @require_admin
    @validate_json_size(10)
    def admin_reset_user_password(user_id):
        data = request.get_json()
        if not data or not data.get('password'):
            return jsonify({'error': 'New password required'}), 400
        
        success, message = User.reset_user_password(user_id, data['password'])
        if success:
            return jsonify({'message': message})
        else:
            return jsonify({'error': message}), 400
=======
def register_routes(app):
    # User info endpoint
    @app.route('/api/user', methods=['GET'])
    @authelia_required
    def get_user():
        user_info = get_user_info()
        return jsonify(user_info)

    # Admin endpoints
    @app.route('/api/admin/users', methods=['GET'])
    @authelia_required
    @admin_required
    def get_all_users():
        users = User.get_all_users()
        return jsonify(users)

    @app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
    @authelia_required
    @admin_required
    def delete_user(user_id):
        if User.delete_user(user_id):
            return '', 204
        return jsonify({'error': 'User not found'}), 404
>>>>>>> 114797d (added authelia)

    # Template routes
    @app.route('/api/templates', methods=['GET'])
    @authelia_required
    def get_templates():
        user_id = get_current_user_id()
        templates = Template.get_all_by_user(user_id)
        return jsonify(templates)

    @app.route('/api/templates', methods=['POST'])
<<<<<<< HEAD
    @jwt_required()
    @validate_json_size(50)  # Limit to 50KB
    @validate_request(TEMPLATE_CREATION_SCHEMA)
=======
    @authelia_required
>>>>>>> 114797d (added authelia)
    def create_template():
        user_id = get_current_user_id()
        data = request.get_json()
        
        template_id = Template.create(user_id, data['name'])
        if template_id is None:
            return jsonify({'error': 'Template name already exists'}), 409
        
        # Create exercises if provided
        exercises = data.get('exercises', [])
        for i, exercise_name in enumerate(exercises):
            TemplateExercise.create(template_id, exercise_name, i)
        
        return jsonify({'id': template_id, 'name': data['name']}), 201

    @app.route('/api/templates/<int:template_id>', methods=['PUT'])
<<<<<<< HEAD
    @jwt_required()
    @validate_json_size(50)  # Limit to 50KB
    @validate_request(TEMPLATE_UPDATE_SCHEMA)
=======
    @authelia_required
>>>>>>> 114797d (added authelia)
    def update_template(template_id):
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Check if template exists and belongs to user
        template = Template.get_by_id(template_id, user_id)
        if not template:
            log_access_denied(user_id, f'template:{template_id}', 'UPDATE')
            return jsonify({'error': 'Template not found'}), 404
        
        # Update template name
        if not Template.update(template_id, user_id, data['name']):
            return jsonify({'error': 'Failed to update template'}), 500
        
        # Update exercises
        if 'exercises' in data:
            TemplateExercise.delete_by_template(template_id)
            for i, exercise_name in enumerate(data['exercises']):
                TemplateExercise.create(template_id, exercise_name, i)
        
        return jsonify({'id': template_id, 'name': data['name']})

    @app.route('/api/templates/<int:template_id>', methods=['DELETE'])
    @authelia_required
    def delete_template(template_id):
        user_id = get_current_user_id()
        
        if not Template.delete(template_id, user_id):
            log_access_denied(user_id, f'template:{template_id}', 'DELETE')
            return jsonify({'error': 'Template not found'}), 404
        
        log_data_access(user_id, 'template', template_id, 'DELETE')
        
        return '', 204

    @app.route('/api/templates/<int:template_id>/exercises', methods=['GET'])
    @authelia_required
    def get_template_exercises(template_id):
        user_id = get_current_user_id()
        
        # Check if template belongs to user
        template = Template.get_by_id(template_id, user_id)
        if not template:
            log_access_denied(user_id, f'template:{template_id}', 'READ_EXERCISES')
            return jsonify({'error': 'Template not found'}), 404
        
        exercises = TemplateExercise.get_by_template(template_id)
        return jsonify(exercises)

    @app.route('/api/templates/<int:template_id>/exercises', methods=['POST'])
    @authelia_required
    def add_template_exercise(template_id):
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Exercise name required'}), 400
        
        # Check if template belongs to user
        if not Template.get_by_id(template_id, user_id):
            return jsonify({'error': 'Template not found'}), 404
        
        # Get current max order_idx
        exercises = TemplateExercise.get_by_template(template_id)
        order_idx = len(exercises)
        
        exercise_id = TemplateExercise.create(template_id, data['name'], order_idx)
        return jsonify({'id': exercise_id, 'name': data['name'], 'order_idx': order_idx}), 201

    # Session routes
    @app.route('/api/sessions/latest/<int:template_exercise_id>', methods=['GET'])
    @authelia_required
    def get_latest_session_exercise(template_exercise_id):
        user_id = get_current_user_id()
        latest = SessionExercise.get_latest_by_template_exercise(template_exercise_id, user_id)
        return jsonify(latest or {})

    @app.route('/api/sessions', methods=['POST'])
<<<<<<< HEAD
    @jwt_required()
    @validate_json_size(500)  # Larger limit for session data
    @validate_request(SESSION_CREATION_SCHEMA)
=======
    @authelia_required
>>>>>>> 114797d (added authelia)
    def create_session():
        user_id = get_current_user_id()
        data = request.get_json()
        
        template_id = data['template_id']
        session_date = data.get('session_date')
        
        # Check if template belongs to user
        if not Template.get_by_id(template_id, user_id):
            return jsonify({'error': 'Template not found'}), 404
        
        session_id = Session.create(user_id, template_id, session_date)
        
        # Create session exercises with ownership validation
        exercises = data.get('exercises', [])
        for exercise in exercises:
            if all(k in exercise for k in ['template_exercise_id', 'weight_kg', 'reps', 'sets']):
                # Validate that the template exercise belongs to the current user
                if not TemplateExercise.validate_ownership(exercise['template_exercise_id'], user_id):
                    return jsonify({'error': f'Template exercise {exercise["template_exercise_id"]} not found or access denied'}), 403
                
                SessionExercise.create(
                    session_id,
                    exercise['template_exercise_id'],
                    exercise['weight_kg'],
                    exercise['reps'],
                    exercise['sets']
                )
        
        return jsonify({'id': session_id}), 201

    @app.route('/api/sessions', methods=['GET'])
    @authelia_required
    def get_sessions():
        user_id = get_current_user_id()
        template_id = request.args.get('template')
        
        if template_id:
            try:
                template_id = int(template_id)
            except ValueError:
                return jsonify({'error': 'Invalid template ID'}), 400
        
        sessions = Session.get_by_user(user_id, template_id)
        
        # Add exercise details to each session
        for session in sessions:
            session['exercises'] = SessionExercise.get_by_session(session['id'])
        
        return jsonify(sessions)

    @app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
    @authelia_required
    def delete_session(session_id):
        user_id = get_current_user_id()
        
        if not Session.delete(session_id, user_id):
            return jsonify({'error': 'Session not found'}), 404
        
        return '', 204

    # Health check endpoint (no auth required)
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy', 
            'service': 'workout-tracker',
            'auth_method': 'authelia'
        }), 200

    # Authentication status endpoint
    @app.route('/api/auth/status', methods=['GET'])
    @authelia_required
    def auth_status():
        user_info = get_user_info()
        return jsonify({
            'authenticated': True,
            'user': user_info
        })

    # Serve static files for PWA
    @app.route('/')
    def serve_index():
        return app.send_static_file('index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return app.send_static_file(path)

# For development
if __name__ == '__main__':
    app = create_app()
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = config[config_name]
    
    if config_name == 'development':
        app.static_folder = '../public'
        print("⚠️  Development mode - Authelia headers will be simulated")
        print("   In production, ensure Authelia is properly configured")
        app.run(debug=config_obj.DEBUG, host=config_obj.HOST, port=config_obj.PORT)
    else:
        print("Use a WSGI server like gunicorn for production")
