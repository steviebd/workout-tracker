import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_EXPIRES_DAYS', 30)))
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'workout.db'
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 8080))

class ProductionConfig(Config):
    """Production configuration."""
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
