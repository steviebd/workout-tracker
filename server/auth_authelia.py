from flask import request, jsonify
from functools import wraps
from models import User
import logging

logger = logging.getLogger(__name__)

def authelia_required(f):
    """
    Decorator to require Authelia authentication.
    Checks for Authelia headers and creates/gets user from database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authelia headers
        remote_user = request.headers.get('Remote-User')
        remote_name = request.headers.get('Remote-Name', remote_user)
        remote_email = request.headers.get('Remote-Email', '')
        remote_groups = request.headers.get('Remote-Groups', '')
        
        # Check if user is authenticated via Authelia
        if not remote_user:
            logger.warning(f"Unauthenticated request from {request.remote_addr}")
            return jsonify({'error': 'Authentication required via Authelia'}), 401
        
        # Get or create user in database
        user = User.get_by_username(remote_user)
        if not user:
            # Create user if they don't exist (they must exist in Authelia first)
            logger.info(f"Creating new user from Authelia: {remote_user}")
            user_id = User.create_from_authelia(
                username=remote_user,
                display_name=remote_name,
                email=remote_email,
                groups=remote_groups
            )
            if not user_id:
                logger.error(f"Failed to create user: {remote_user}")
                return jsonify({'error': 'Failed to create user'}), 500
            
            user = User.get_by_username(remote_user)
        else:
            # Update user info from Authelia headers
            User.update_from_authelia(
                user['id'],
                display_name=remote_name,
                email=remote_email,
                groups=remote_groups
            )
        
        # Add user info to request context
        request.current_user = user
        request.current_user_id = user['id']
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get the current authenticated user from request context."""
    return getattr(request, 'current_user', None)

def get_current_user_id():
    """Get the current authenticated user ID from request context."""
    return getattr(request, 'current_user_id', None)

def check_user_permission(required_groups=None):
    """
    Check if the current user has required permissions.
    
    Args:
        required_groups (list): List of required groups for access
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not required_groups:
        return True
    
    user = get_current_user()
    if not user:
        return False
    
    user_groups = user.get('groups', '').split(',')
    user_groups = [group.strip() for group in user_groups if group.strip()]
    
    # Check if user has any of the required groups
    return any(group in user_groups for group in required_groups)

def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_user_permission(['admin', 'administrators']):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function

def get_user_info():
    """Get current user information for API responses."""
    user = get_current_user()
    if not user:
        return None
    
    return {
        'id': user['id'],
        'username': user['username'],
        'display_name': user.get('display_name', user['username']),
        'email': user.get('email', ''),
        'groups': user.get('groups', '').split(',') if user.get('groups') else []
    }
