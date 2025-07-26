"""
Security logging module for audit trail and monitoring.
"""

import logging
import json
import os
from datetime import datetime
from flask import request, g
from functools import wraps

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Create file handler for security events
log_dir = os.environ.get('LOG_DIR', 'logs')
os.makedirs(log_dir, exist_ok=True)

security_file_handler = logging.FileHandler(os.path.join(log_dir, 'security.log'))
security_file_handler.setLevel(logging.INFO)

# Create console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create JSON formatter for structured logging
class SecurityFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'event_type': getattr(record, 'event_type', 'UNKNOWN'),
            'message': record.getMessage(),
            'user_id': getattr(record, 'user_id', None),
            'username': getattr(record, 'username', None),
            'ip_address': getattr(record, 'ip_address', None),
            'user_agent': getattr(record, 'user_agent', None),
            'endpoint': getattr(record, 'endpoint', None),
            'method': getattr(record, 'method', None),
            'status_code': getattr(record, 'status_code', None),
            'additional_data': getattr(record, 'additional_data', {})
        }
        return json.dumps(log_entry)

formatter = SecurityFormatter()
security_file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

security_logger.addHandler(security_file_handler)
security_logger.addHandler(console_handler)

# Prevent duplicate logs from propagating to root logger
security_logger.propagate = False

def get_request_info():
    """Extract request information for logging."""
    return {
        'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
        'user_agent': request.headers.get('User-Agent', ''),
        'endpoint': request.endpoint,
        'method': request.method
    }

def log_auth_success(user_id, username):
    """Log successful authentication."""
    info = get_request_info()
    security_logger.info(
        f"Authentication successful for user {username}",
        extra={
            'event_type': 'AUTH_SUCCESS',
            'user_id': user_id,
            'username': username,
            **info
        }
    )

def log_auth_failure(username, reason='Invalid credentials'):
    """Log failed authentication attempt."""
    info = get_request_info()
    security_logger.warning(
        f"Authentication failed for user {username}: {reason}",
        extra={
            'event_type': 'AUTH_FAILURE',
            'username': username,
            'additional_data': {'failure_reason': reason},
            **info
        }
    )

def log_rate_limit_exceeded(limit_type='general'):
    """Log rate limit exceeded events."""
    info = get_request_info()
    security_logger.warning(
        f"Rate limit exceeded: {limit_type}",
        extra={
            'event_type': 'RATE_LIMIT_EXCEEDED',
            'additional_data': {'limit_type': limit_type},
            **info
        }
    )

def log_access_denied(user_id, resource, action):
    """Log access denied events."""
    info = get_request_info()
    security_logger.warning(
        f"Access denied: User {user_id} attempted {action} on {resource}",
        extra={
            'event_type': 'ACCESS_DENIED',
            'user_id': user_id,
            'additional_data': {'resource': resource, 'action': action},
            **info
        }
    )

def log_data_access(user_id, resource_type, resource_id, action):
    """Log data access events."""
    info = get_request_info()
    security_logger.info(
        f"Data access: User {user_id} performed {action} on {resource_type} {resource_id}",
        extra={
            'event_type': 'DATA_ACCESS',
            'user_id': user_id,
            'additional_data': {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action
            },
            **info
        }
    )

def log_security_event(event_type, message, user_id=None, additional_data=None):
    """Log general security events."""
    info = get_request_info()
    security_logger.warning(
        message,
        extra={
            'event_type': event_type,
            'user_id': user_id,
            'additional_data': additional_data or {},
            **info
        }
    )

def security_audit(action):
    """Decorator to automatically log data access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                # Log successful access
                if hasattr(g, 'current_user_id'):
                    log_data_access(
                        user_id=g.current_user_id,
                        resource_type=request.endpoint,
                        resource_id=kwargs.get('id', 'unknown'),
                        action=action
                    )
                return result
            except Exception as e:
                # Log failed access attempts
                if hasattr(g, 'current_user_id'):
                    log_security_event(
                        'DATA_ACCESS_ERROR',
                        f"Error during {action}: {str(e)}",
                        user_id=g.current_user_id,
                        additional_data={'error': str(e)}
                    )
                raise
        return decorated_function
    return decorator
