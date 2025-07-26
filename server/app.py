import os
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required
from flask_cors import CORS
from config import config
from db import init_db
from auth import login, get_current_user_id
from models import Template, TemplateExercise, Session, SessionExercise

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = config[config_name]()  # Initialize config instance
    app.config.from_object(config_obj)
    
    # Configure static files (use absolute path)
    app.static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public'))
    
    # Initialize extensions
    jwt = JWTManager(app)
    
    # Configure CORS with security
    CORS(app, 
         origins=config_obj.CORS_ORIGINS,
         supports_credentials=config_obj.CORS_SUPPORTS_CREDENTIALS,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize database
    init_db()
    
    # Register routes
    register_routes(app)
    
    return app

def register_routes(app):
    # Auth routes
    @app.route('/api/auth/login', methods=['POST'])
    def auth_login():
        return login()

    # Template routes
    @app.route('/api/templates', methods=['GET'])
    @jwt_required()
    def get_templates():
        user_id = get_current_user_id()
        templates = Template.get_all_by_user(user_id)
        return jsonify(templates)

    @app.route('/api/templates', methods=['POST'])
    @jwt_required()
    def create_template():
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Template name required'}), 400
        
        template_id = Template.create(user_id, data['name'])
        if template_id is None:
            return jsonify({'error': 'Template name already exists'}), 409
        
        # Create exercises if provided
        exercises = data.get('exercises', [])
        for i, exercise_name in enumerate(exercises):
            TemplateExercise.create(template_id, exercise_name, i)
        
        return jsonify({'id': template_id, 'name': data['name']}), 201

    @app.route('/api/templates/<int:template_id>', methods=['PUT'])
    @jwt_required()
    def update_template(template_id):
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Template name required'}), 400
        
        # Check if template exists and belongs to user
        if not Template.get_by_id(template_id, user_id):
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
    @jwt_required()
    def delete_template(template_id):
        user_id = get_current_user_id()
        
        if not Template.delete(template_id, user_id):
            return jsonify({'error': 'Template not found'}), 404
        
        return '', 204

    @app.route('/api/templates/<int:template_id>/exercises', methods=['GET'])
    @jwt_required()
    def get_template_exercises(template_id):
        user_id = get_current_user_id()
        
        # Check if template belongs to user
        if not Template.get_by_id(template_id, user_id):
            return jsonify({'error': 'Template not found'}), 404
        
        exercises = TemplateExercise.get_by_template(template_id)
        return jsonify(exercises)

    @app.route('/api/templates/<int:template_id>/exercises', methods=['POST'])
    @jwt_required()
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
    @jwt_required()
    def get_latest_session_exercise(template_exercise_id):
        user_id = get_current_user_id()
        latest = SessionExercise.get_latest_by_template_exercise(template_exercise_id, user_id)
        return jsonify(latest or {})

    @app.route('/api/sessions', methods=['POST'])
    @jwt_required()
    def create_session():
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or not data.get('template_id'):
            return jsonify({'error': 'Template ID required'}), 400
        
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
    @jwt_required()
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
    @jwt_required()
    def delete_session(session_id):
        user_id = get_current_user_id()
        
        if not Session.delete(session_id, user_id):
            return jsonify({'error': 'Session not found'}), 404
        
        return '', 204

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'workout-tracker'}), 200

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
        app.run(debug=config_obj.DEBUG, host=config_obj.HOST, port=config_obj.PORT)
    else:
        print("Use a WSGI server like gunicorn for production")
