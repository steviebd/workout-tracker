#!/usr/bin/env python3
"""
Security Configuration Generator for Workout Tracker PWA
Generates secure secrets and validates configuration.
"""

import secrets
import os
import sys

def generate_secret_key(length=32):
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(length)

def validate_domain(domain):
    """Basic domain validation."""
    if not domain:
        return False
    if domain.startswith('http://') and not domain.startswith('http://localhost'):
        print(f"⚠️  Warning: HTTP domain detected: {domain}")
        print("   Consider using HTTPS for production")
    return True

def main():
    print("🔐 Workout Tracker Security Configuration Generator")
    print("=" * 50)
    
    # Generate secure secrets
    secret_key = generate_secret_key(32)
    jwt_secret = generate_secret_key(32)
    
    print("\n✅ Generated secure secrets:")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    # Get CORS configuration
    print("\n🌐 CORS Configuration:")
    print("Enter your domain(s) for CORS origins (comma-separated)")
    print("Examples:")
    print("  Production: https://yourdomain.com")
    print("  Development: http://localhost:8080")
    
    cors_input = input("CORS Origins: ").strip()
    if cors_input:
        domains = [d.strip() for d in cors_input.split(',')]
        for domain in domains:
            validate_domain(domain)
        cors_origins = ','.join(domains)
    else:
        cors_origins = "http://localhost:8080"
        print(f"Using default: {cors_origins}")
    
    # JWT expiry
    print("\n⏰ JWT Token Configuration:")
    jwt_minutes = input("JWT expiry in minutes (default: 15): ").strip()
    if not jwt_minutes:
        jwt_minutes = "15"
    
    # Environment type
    print("\n🏭 Environment Configuration:")
    env_type = input("Environment type (development/production) [production]: ").strip()
    if not env_type:
        env_type = "production"
    
    # Generate .env file
    env_content = f"""# Workout Tracker Environment Configuration
# Generated on {os.popen('date').read().strip()}
# SECURITY: Keep this file secure and never commit to git

# SECURITY SETTINGS (REQUIRED)
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}

# JWT Configuration
JWT_EXPIRES_MINUTES={jwt_minutes}

# Database Configuration
DATABASE_PATH={"workout.db" if env_type == "development" else "/opt/workout-tracker/data/workout.db"}

# CORS Configuration
CORS_ORIGINS={cors_origins}
CORS_SUPPORTS_CREDENTIALS=false

# Flask Environment
FLASK_ENV={env_type}

# Server Configuration
PORT=8080

# Skip secret validation in development only
SKIP_SECRET_VALIDATION={"true" if env_type == "development" else "false"}
"""
    
    print("\n📝 Generated .env configuration:")
    print("-" * 40)
    print(env_content)
    print("-" * 40)
    
    # Save to file
    save_file = input("\nSave to .env file? (y/N): ").strip().lower()
    if save_file == 'y':
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Configuration saved to .env")
        print("⚠️  Remember to:")
        print("   1. Review the configuration")
        print("   2. Update your domain in CORS_ORIGINS")
        print("   3. Never commit .env to git")
        print("   4. Set appropriate file permissions: chmod 600 .env")
    
    # Docker environment
    print("\n🐳 For Docker deployment, set these environment variables:")
    print("export SECRET_KEY=" + secret_key)
    print("export JWT_SECRET_KEY=" + jwt_secret)
    print("export CORS_ORIGINS=" + cors_origins)
    print("export JWT_EXPIRES_MINUTES=" + jwt_minutes)
    
    print("\n🎉 Security configuration complete!")
    print("💡 Run this script again to generate new secrets for production rotation.")

if __name__ == "__main__":
    main()
