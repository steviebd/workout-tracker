from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, PasswordResetToken
from security_logger import log_auth_success, log_auth_failure, log_security_event
from validation import validate_username
from email_service import email_service
from functools import wraps

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
    return jsonify({
        'access_token': access_token, 
        'user_id': user['id'],
        'role': user['role'],
        'must_change_password': user['must_change_password']
    }), 200

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

def change_password():
    """Change user password."""
    data = request.get_json()
    if not data or not all(k in data for k in ['current_password', 'new_password']):
        log_security_event('PASSWORD_CHANGE_ATTEMPT', 'Missing required fields')
        return jsonify({'error': 'Current password and new password required'}), 400
    
    user_id = get_current_user_id()
    current_password = data['current_password']
    new_password = data['new_password']
    
    try:
        success, message = User.change_password(user_id, current_password, new_password)
        
        if success:
            log_security_event('PASSWORD_CHANGE_SUCCESS', f'Password changed for user {user_id}', user_id=user_id)
            return jsonify({'message': message}), 200
        else:
            log_security_event('PASSWORD_CHANGE_FAILURE', f'Password change failed for user {user_id}: {message}', user_id=user_id)
            return jsonify({'error': message}), 400
            
    except Exception as e:
        log_security_event('PASSWORD_CHANGE_ERROR', f'Password change error for user {user_id}: {str(e)}', user_id=user_id)
        return jsonify({'error': 'Password change failed'}), 500

def get_password_policy():
    """Get current password policy requirements."""
    policy = User.get_password_policy()
    
    # Create user-friendly policy description
    requirements = []
    if policy['min_length'] > 0:
        requirements.append(f"At least {policy['min_length']} characters")
    if policy['max_length'] < 999:
        requirements.append(f"No more than {policy['max_length']} characters")
    if policy['require_lowercase']:
        requirements.append("At least one lowercase letter")
    if policy['require_uppercase']:
        requirements.append("At least one uppercase letter")
    if policy['require_numbers']:
        requirements.append("At least one number")
    if policy['require_special']:
        requirements.append("At least one special character")
    if policy['block_common']:
        requirements.append("Cannot be a common password")
    
    return jsonify({
        'requirements': requirements,
        'policy': policy
    }), 200

def get_current_user_id():
    return int(get_jwt_identity())

def get_current_user():
    """Get current user data."""
    user_id = get_current_user_id()
    return User.get_by_id(user_id)

def require_admin(f):
    """Decorator to require admin role."""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user['role'] != 'admin':
            log_security_event('ADMIN_ACCESS_DENIED', f'User {user["id"] if user else "unknown"} attempted admin action')
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def forgot_password():
    """Initiate password reset process."""
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({'error': 'Email address required'}), 400
    
    email = data['email'].lower().strip()
    user = User.get_by_email(email)
    
    if user:
        # Create reset token
        token = PasswordResetToken.create(user['id'])
        
        # Send email
        success, message = email_service.send_password_reset_email(
            user['email'], user['username'], token
        )
        
        if not success:
            log_security_event('PASSWORD_RESET_EMAIL_FAILED', f'Failed to send reset email to {email}')
            return jsonify({'error': 'Failed to send reset email'}), 500
    
    # Always return success to prevent email enumeration
    return jsonify({'message': 'If an account with that email exists, a password reset link has been sent'}), 200

def reset_password():
    """Reset password with token."""
    data = request.get_json()
    if not data or not data.get('token') or not data.get('password'):
        return jsonify({'error': 'Token and new password required'}), 400
    
    token = data['token']
    new_password = data['password']
    
    success, message = PasswordResetToken.reset_password_with_token(token, new_password)
    
    if success:
        log_security_event('PASSWORD_RESET_SUCCESS', f'Password reset successful for token')
        return jsonify({'message': message}), 200
    else:
        log_security_event('PASSWORD_RESET_FAILED', f'Password reset failed: {message}')
        return jsonify({'error': message}), 400
