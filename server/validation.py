"""
Input validation module for API endpoints.
"""

import re
from functools import wraps
from flask import request, jsonify

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_string(value, name, min_length=1, max_length=255, pattern=None, required=True):
    """Validate string input."""
    if value is None:
        if required:
            raise ValidationError(f"{name} is required")
        return True
    
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")
    
    # Trim whitespace
    value = value.strip()
    
    if required and len(value) == 0:
        raise ValidationError(f"{name} cannot be empty")
    
    if len(value) < min_length:
        raise ValidationError(f"{name} must be at least {min_length} characters long")
    
    if len(value) > max_length:
        raise ValidationError(f"{name} must be no longer than {max_length} characters")
    
    if pattern and not re.match(pattern, value):
        raise ValidationError(f"{name} format is invalid")
    
    # Check for potential XSS/injection patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]
    
    for dangerous_pattern in dangerous_patterns:
        if re.search(dangerous_pattern, value, re.IGNORECASE):
            raise ValidationError(f"{name} contains potentially dangerous content")
    
    return True

def validate_integer(value, name, min_value=None, max_value=None, required=True):
    """Validate integer input."""
    if value is None:
        if required:
            raise ValidationError(f"{name} is required")
        return True
    
    try:
        value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid integer")
    
    if min_value is not None and value < min_value:
        raise ValidationError(f"{name} must be at least {min_value}")
    
    if max_value is not None and value > max_value:
        raise ValidationError(f"{name} must be no greater than {max_value}")
    
    return True

def validate_float(value, name, min_value=None, max_value=None, required=True):
    """Validate float input."""
    if value is None:
        if required:
            raise ValidationError(f"{name} is required")
        return True
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid number")
    
    if min_value is not None and value < min_value:
        raise ValidationError(f"{name} must be at least {min_value}")
    
    if max_value is not None and value > max_value:
        raise ValidationError(f"{name} must be no greater than {max_value}")
    
    return True

def validate_username(username):
    """Validate username format."""
    if not username:
        raise ValidationError("Username is required")
    
    # Username validation: 3-50 chars, alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', username):
        raise ValidationError("Username must be 3-50 characters long and contain only letters, numbers, underscore, or hyphen")
    
    # Check for reserved usernames
    reserved_usernames = ['admin', 'root', 'system', 'test', 'api', 'www', 'mail', 'support']
    if username.lower() in reserved_usernames:
        raise ValidationError("Username is reserved and cannot be used")
    
    return True

def validate_template_name(name):
    """Validate workout template name."""
    validate_string(name, "Template name", min_length=1, max_length=100)
    
    # Additional check for template names
    if name.strip() in ['', 'undefined', 'null', 'default']:
        raise ValidationError("Template name cannot be a reserved word")
    
    return True

def validate_exercise_name(name):
    """Validate exercise name."""
    validate_string(name, "Exercise name", min_length=1, max_length=100)
    return True

def validate_workout_data(weight_kg, reps, sets):
    """Validate workout data inputs."""
    validate_float(weight_kg, "Weight", min_value=0, max_value=1000)
    validate_integer(reps, "Reps", min_value=1, max_value=999)
    validate_integer(sets, "Sets", min_value=1, max_value=50)
    return True

def validate_json_size(max_size_kb=100):
    """Validate JSON request size."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            content_length = request.content_length
            if content_length and content_length > max_size_kb * 1024:
                return jsonify({'error': f'Request too large (max {max_size_kb}KB)'}), 413
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_request(validation_schema):
    """Decorator to validate request data against a schema."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({'error': 'Invalid JSON data'}), 400
                
                # Apply validation schema
                for field, validators in validation_schema.items():
                    value = data.get(field)
                    for validator in validators:
                        validator(value)
                
                return f(*args, **kwargs)
            
            except ValidationError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                return jsonify({'error': 'Validation failed'}), 400
        
        return decorated_function
    return decorator

# Common validation schemas
TEMPLATE_CREATION_SCHEMA = {
    'name': [validate_template_name],
    'exercises': [lambda x: True if x is None else all(validate_exercise_name(ex) for ex in x)]
}

TEMPLATE_UPDATE_SCHEMA = {
    'name': [validate_template_name]
}

SESSION_CREATION_SCHEMA = {
    'template_id': [lambda x: validate_integer(x, "Template ID", min_value=1)],
    'exercises': [lambda x: True if x is None else validate_exercise_list(x)]
}

def validate_exercise_list(exercises):
    """Validate list of exercises for session creation."""
    if not isinstance(exercises, list):
        raise ValidationError("Exercises must be a list")
    
    if len(exercises) > 50:  # Reasonable limit
        raise ValidationError("Too many exercises (max 50 per session)")
    
    for i, exercise in enumerate(exercises):
        if not isinstance(exercise, dict):
            raise ValidationError(f"Exercise {i+1} must be an object")
        
        required_fields = ['template_exercise_id', 'weight_kg', 'reps', 'sets']
        for field in required_fields:
            if field not in exercise:
                raise ValidationError(f"Exercise {i+1} missing required field: {field}")
        
        # Validate each field
        validate_integer(exercise['template_exercise_id'], f"Exercise {i+1} template_exercise_id", min_value=1)
        validate_workout_data(exercise['weight_kg'], exercise['reps'], exercise['sets'])
    
    return True
