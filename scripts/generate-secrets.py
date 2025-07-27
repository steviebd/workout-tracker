#!/usr/bin/env python3
"""
Security Configuration Generator for Workout Tracker PWA
Generates secure secrets and validates configuration.
"""

import secrets
import os
import sys
import string

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

def generate_admin_password():
    """Generate a secure temporary password for admin (Docker-safe)."""
    # Use only letters and numbers for maximum compatibility
    # Add one @ symbol to meet special character requirement
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(11))
    password = 'A' + password[1:] if not any(c.isupper() for c in password) else password
    password = 'a' + password[1:] if not any(c.islower() for c in password) else password
    password = '1' + password[1:] if not any(c.isdigit() for c in password) else password
    password = password + '@'  # Add @ at the end to meet special char requirement
    return password

def get_email_config(env_type, cors_origins):
    """Get email configuration for password reset functionality."""
    print("\n📧 Email Configuration (for password reset):")
    print("Configure SMTP settings for password reset emails")
    
    setup_email = input("Setup email configuration? (Y/n): ").strip().lower()
    if setup_email == 'n':
        return {}
    
    print("\nChoose email provider:")
    print("1. Gmail")
    print("2. SendGrid") 
    print("3. Custom SMTP")
    print("4. Local SMTP (testing only)")
    
    choice = input("Select option (1-4): ").strip()
    
    email_config = {}
    
    if choice == '1':  # Gmail
        email_config['SMTP_SERVER'] = 'smtp.gmail.com'
        email_config['SMTP_PORT'] = '587'
        email_config['SMTP_USE_TLS'] = 'true'
        email_config['SMTP_USERNAME'] = input("Gmail address: ").strip()
        email_config['SMTP_PASSWORD'] = input("Gmail app password: ").strip()
    elif choice == '2':  # SendGrid
        email_config['SMTP_SERVER'] = 'smtp.sendgrid.net'
        email_config['SMTP_PORT'] = '587'
        email_config['SMTP_USE_TLS'] = 'true'
        email_config['SMTP_USERNAME'] = 'apikey'
        email_config['SMTP_PASSWORD'] = input("SendGrid API key: ").strip()
    elif choice == '3':  # Custom
        email_config['SMTP_SERVER'] = input("SMTP server: ").strip()
        email_config['SMTP_PORT'] = input("SMTP port (587): ").strip() or '587'
        email_config['SMTP_USE_TLS'] = 'true' if input("Use TLS? (Y/n): ").strip().lower() != 'n' else 'false'
        email_config['SMTP_USERNAME'] = input("SMTP username: ").strip()
        email_config['SMTP_PASSWORD'] = input("SMTP password: ").strip()
    else:  # Local SMTP
        email_config['SMTP_SERVER'] = 'localhost'
        email_config['SMTP_PORT'] = '25'
        email_config['SMTP_USE_TLS'] = 'false'
        print("Using local SMTP (no authentication)")
    
    # Common email settings
    try:
        default_from = f"noreply@{cors_origins.split('://')[-1].split(',')[0].split('/')[0]}"
    except:
        default_from = "noreply@workout-tracker.local"
    from_email_input = input(f"From email [{default_from}]: ").strip()
    email_config['FROM_EMAIL'] = from_email_input if from_email_input else default_from
    
    return email_config

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
    
    # Environment type
    print("\n🏭 Environment Configuration:")
    env_type = input("Environment type (development/production) [production]: ").strip()
    if not env_type:
        env_type = "production"
    
    # JWT expiry
    print("\n⏰ JWT Token Configuration:")
    jwt_minutes = input("JWT expiry in minutes (default: 15): ").strip()
    if not jwt_minutes:
        jwt_minutes = "15"
    
    # Password policy configuration
    print("\n🔒 Password Policy Configuration:")
    use_default_policy = input("Use default password policy? (Y/n): ").strip().lower()
    
    if use_default_policy != 'n':
        password_policy = {
            'min_length': 8,
            'max_length': 128,
            'require_uppercase': 'true',
            'require_lowercase': 'true',
            'require_numbers': 'true',
            'require_special': 'true',
            'block_common': 'true'
        }
        print("Using default policy: 8-128 chars, requires upper/lower/number/special")
    else:
        password_policy = {
            'min_length': input("Minimum length (default: 8): ").strip() or 8,
            'max_length': input("Maximum length (default: 128): ").strip() or 128,
            'require_uppercase': 'true' if input("Require uppercase? (Y/n): ").strip().lower() != 'n' else 'false',
            'require_lowercase': 'true' if input("Require lowercase? (Y/n): ").strip().lower() != 'n' else 'false',
            'require_numbers': 'true' if input("Require numbers? (Y/n): ").strip().lower() != 'n' else 'false',
            'require_special': 'true' if input("Require special chars? (Y/n): ").strip().lower() != 'n' else 'false',
            'block_common': 'true' if input("Block common passwords? (Y/n): ").strip().lower() != 'n' else 'false'
        }
    
    # Generate admin password
    admin_password = generate_admin_password()
    print(f"\n👤 Generated temporary admin password: {admin_password}")
    
    # Rate limiting configuration
    print("\n🚦 Rate Limiting Configuration:")
    print("Configure API rate limits for security protection")
    use_defaults = input("Use default rate limits? (Y/n): ").strip().lower()
    
    if use_defaults != 'n':
        if env_type == "development":
            rate_limit_default = "2000 per hour, 200 per minute"
            rate_limit_login = "10 per minute"
            rate_limit_register = "5 per minute"
        else:
            rate_limit_default = "1000 per hour, 100 per minute"
            rate_limit_login = "5 per minute"
            rate_limit_register = "3 per minute"
        print(f"Using defaults for {env_type}:")
        print(f"  General API: {rate_limit_default}")
        print(f"  Login: {rate_limit_login}")
        print(f"  Register: {rate_limit_register}")
    else:
        print("Enter custom rate limits (format: 'X per minute' or 'X per hour, Y per minute'):")
        rate_limit_default = input("General API limits: ").strip() or "1000 per hour, 100 per minute"
        rate_limit_login = input("Login endpoint limit: ").strip() or "5 per minute"
        rate_limit_register = input("Register endpoint limit: ").strip() or "3 per minute"
    
    # Get email configuration
    email_config = get_email_config(env_type, cors_origins)

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
DATABASE_PATH=workout.db

# CORS Configuration
CORS_ORIGINS={cors_origins}
CORS_SUPPORTS_CREDENTIALS=false

# Rate Limiting Configuration
RATE_LIMIT_DEFAULT="{rate_limit_default}"
RATE_LIMIT_AUTH_LOGIN="{rate_limit_login}"
RATE_LIMIT_AUTH_REGISTER="{rate_limit_register}"
RATE_LIMIT_STORAGE_URI=memory://

# Password Policy Configuration
PASSWORD_MIN_LENGTH={password_policy['min_length']}
PASSWORD_MAX_LENGTH={password_policy['max_length']}
PASSWORD_REQUIRE_UPPERCASE={password_policy['require_uppercase']}
PASSWORD_REQUIRE_LOWERCASE={password_policy['require_lowercase']}
PASSWORD_REQUIRE_NUMBERS={password_policy['require_numbers']}
PASSWORD_REQUIRE_SPECIAL={password_policy['require_special']}
PASSWORD_BLOCK_COMMON={password_policy['block_common']}

# Flask Environment
FLASK_ENV={env_type}

# Server Configuration
PORT=8080

# Skip secret validation in development only
SKIP_SECRET_VALIDATION={"true" if env_type == "development" else "false"}

# Admin User Configuration (for seed.py reference)
ADMIN_TEMP_PASSWORD={admin_password}

# Application URL (used for password reset emails)
APP_URL={cors_origins.split(',')[0]}
"""

    # Add email configuration if provided
    if email_config:
        env_content += "\n# Email Configuration (SMTP)\n"
        for key, value in email_config.items():
            env_content += f"{key}={value}\n"
    
    print("\n📝 Generated .env configuration:")
    print("-" * 40)
    print(env_content)
    print("-" * 40)
    
    print("⚠️  Remember to:")
    print("   1. Review the configuration")
    print("   2. Update your domain in CORS_ORIGINS if needed")
    print("   3. Never commit .env to git")
    print("   4. Test the admin login with the credentials above")
    if email_config:
        print("   5. Test email functionality with password reset")
        
    # Docker ready message
    print(f"\n🐳 Ready for Docker Compose!")
    print("Start with: docker-compose up -d")
    
    # Docker environment
    print("\n🐳 For Docker deployment, set these environment variables:")
    print("export SECRET_KEY=" + secret_key)
    print("export JWT_SECRET_KEY=" + jwt_secret)
    print("export CORS_ORIGINS=" + cors_origins)
    print("export JWT_EXPIRES_MINUTES=" + jwt_minutes)
    print("export RATE_LIMIT_DEFAULT='" + rate_limit_default + "'")
    print("export RATE_LIMIT_AUTH_LOGIN='" + rate_limit_login + "'")
    print("export RATE_LIMIT_AUTH_REGISTER='" + rate_limit_register + "'")
    
    print("\n🎉 Security configuration complete!")
    print("💡 Run this script again to generate new secrets for production rotation.")

if __name__ == "__main__":
    main()
