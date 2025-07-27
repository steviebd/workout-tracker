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
    print("Configure password complexity requirements")
    use_default_password_policy = input("Use default password policy? (Y/n): ").strip().lower()
    
    if use_default_password_policy != 'n':
        if env_type == "development":
            password_policy = {
                'min_length': '6',
                'max_length': '128',
                'require_uppercase': 'false',
                'require_lowercase': 'false', 
                'require_numbers': 'false',
                'require_special': 'false',
                'block_common': 'true'
            }
            print("Using lenient development defaults:")
        else:
            password_policy = {
                'min_length': '8',
                'max_length': '128',
                'require_uppercase': 'true',
                'require_lowercase': 'true',
                'require_numbers': 'true',
                'require_special': 'true',
                'block_common': 'true'
            }
            print("Using strict production defaults:")
        
        print(f"  Minimum length: {password_policy['min_length']} characters")
        print(f"  Maximum length: {password_policy['max_length']} characters")
        print(f"  Require uppercase: {password_policy['require_uppercase']}")
        print(f"  Require lowercase: {password_policy['require_lowercase']}")
        print(f"  Require numbers: {password_policy['require_numbers']}")
        print(f"  Require special chars: {password_policy['require_special']}")
        print(f"  Block common passwords: {password_policy['block_common']}")
    else:
        print("\nCustom password policy:")
        password_policy = {
            'min_length': input("Minimum password length [8]: ").strip() or '8',
            'max_length': input("Maximum password length [128]: ").strip() or '128',
            'require_uppercase': 'true' if input("Require uppercase letters? (Y/n): ").strip().lower() != 'n' else 'false',
            'require_lowercase': 'true' if input("Require lowercase letters? (Y/n): ").strip().lower() != 'n' else 'false',
            'require_numbers': 'true' if input("Require numbers? (Y/n): ").strip().lower() != 'n' else 'false',
            'require_special': 'true' if input("Require special characters? (Y/n): ").strip().lower() != 'n' else 'false',
            'block_common': 'true' if input("Block common passwords? (Y/n): ").strip().lower() != 'n' else 'false'
        }
    
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

# Rate Limiting Configuration
RATE_LIMIT_DEFAULT={rate_limit_default}
RATE_LIMIT_AUTH_LOGIN={rate_limit_login}
RATE_LIMIT_AUTH_REGISTER={rate_limit_register}
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
    print("export RATE_LIMIT_DEFAULT='" + rate_limit_default + "'")
    print("export RATE_LIMIT_AUTH_LOGIN='" + rate_limit_login + "'")
    print("export RATE_LIMIT_AUTH_REGISTER='" + rate_limit_register + "'")
    
    print("\n🎉 Security configuration complete!")
    print("💡 Run this script again to generate new secrets for production rotation.")

if __name__ == "__main__":
    main()
