import os
import sys
from datetime import timedelta

class Config:
    """Base configuration."""
    def __init__(self):
        self._validate_secrets()
    
    def _validate_secrets(self):
        """Validate that production secrets are set properly."""
        secret_key = os.environ.get('SECRET_KEY')
        jwt_secret = os.environ.get('JWT_SECRET_KEY')
        
        # Check for default/weak secrets
        if not secret_key or secret_key in ['dev-secret-key-change-in-production', 'change-this-secret-key']:
            print("❌ SECURITY ERROR: SECRET_KEY not set or using default value!")
            print("   Set environment variable: SECRET_KEY=your-secure-random-key")
            sys.exit(1)
            
        if not jwt_secret or jwt_secret in ['jwt-secret-key-change-in-production', 'change-this-jwt-secret']:
            print("❌ SECURITY ERROR: JWT_SECRET_KEY not set or using default value!")
            print("   Set environment variable: JWT_SECRET_KEY=your-secure-jwt-key")
            sys.exit(1)
            
        if len(secret_key) < 32:
            print("❌ SECURITY ERROR: SECRET_KEY must be at least 32 characters long!")
            sys.exit(1)
            
        if len(jwt_secret) < 32:
            print("❌ SECURITY ERROR: JWT_SECRET_KEY must be at least 32 characters long!")
            sys.exit(1)
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get('JWT_EXPIRES_MINUTES', 15)))
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'workout.db'
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_SUPPORTS_CREDENTIALS = os.environ.get('CORS_SUPPORTS_CREDENTIALS', 'false').lower() == 'true'
    
    # Rate Limiting Configuration
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '1000 per hour, 100 per minute')
    RATE_LIMIT_AUTH_LOGIN = os.environ.get('RATE_LIMIT_AUTH_LOGIN', '5 per minute')
    RATE_LIMIT_AUTH_REGISTER = os.environ.get('RATE_LIMIT_AUTH_REGISTER', '3 per minute')
    RATE_LIMIT_STORAGE_URI = os.environ.get('RATE_LIMIT_STORAGE_URI', 'memory://')
    
class DevelopmentConfig(Config):
    """Development configuration."""
    def __init__(self):
        # Skip secret validation in development if explicitly allowed
        if os.environ.get('SKIP_SECRET_VALIDATION') != 'true':
            super().__init__()
    
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 8080))
    
    # Development CORS - localhost for testing
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8080').split(',')
    
    # Development rate limiting - more lenient
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '2000 per hour, 200 per minute')
    RATE_LIMIT_AUTH_LOGIN = os.environ.get('RATE_LIMIT_AUTH_LOGIN', '10 per minute')
    RATE_LIMIT_AUTH_REGISTER = os.environ.get('RATE_LIMIT_AUTH_REGISTER', '5 per minute')

class ProductionConfig(Config):
    """Production configuration."""
    def __init__(self):
        super().__init__()
        # Enforce production security
        if os.environ.get('FLASK_ENV') == 'development':
            print("❌ SECURITY ERROR: FLASK_ENV=development not allowed in production!")
            print("   Set FLASK_ENV=production")
            sys.exit(1)
    
    DEBUG = False
    HOST = '127.0.0.1'  # Only bind to localhost in production (nginx proxy)
    PORT = int(os.environ.get('PORT', 8080))
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or '/opt/workout-tracker/data/workout.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
