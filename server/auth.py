from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User
from security_logger import log_auth_success, log_auth_failure, log_security_event
from validation import validate_username

def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        log_auth_failure('unknown', 'Missing username or password')
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    user = User.verify_password(username, data['password'])
    if not user:
        log_auth_failure(username, 'Invalid credentials')
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Log successful authentication
    log_auth_success(user['id'], username)
    
    access_token = create_access_token(identity=str(user['id']))
    return jsonify({'access_token': access_token, 'user_id': user['id']}), 200

def register():
    """User registration with validation."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        log_security_event('REGISTRATION_ATTEMPT', 'Missing username or password')
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    try:
        # Validate username
        validate_username(username)
        
        # Create user (this will validate password strength)
        user_id = User.create(username, password)
        
        if user_id is None:
            log_security_event('REGISTRATION_FAILURE', f'Username already exists: {username}')
            return jsonify({'error': 'Username already exists'}), 409
        
        log_security_event('REGISTRATION_SUCCESS', f'New user registered: {username}', user_id=user_id)
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
        
    except ValueError as e:
        # Password validation error
        log_security_event('REGISTRATION_FAILURE', f'Password validation failed for {username}: {str(e)}')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        log_security_event('REGISTRATION_ERROR', f'Registration error for {username}: {str(e)}')
        return jsonify({'error': 'Registration failed'}), 500

def get_current_user_id():
    return int(get_jwt_identity())
