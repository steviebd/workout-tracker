# Security Setup Guide - Workout Tracker PWA

This guide covers the critical security configurations implemented to address the security review findings.

## 🚨 Critical Security Updates

### 1. Secure Secret Management

**What was fixed:** Hard-coded default secrets that could compromise production deployments.

**New behavior:**
- Application **will not start** with default or weak secrets
- Secrets must be at least 32 characters long
- Clear error messages guide proper configuration

**Setup:**

```bash
# Option 1: Use the secret generator script
python3 scripts/generate-secrets.py

# Option 2: Generate manually
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

### 2. CORS Security Configuration

**What was fixed:** Permissive CORS allowing any origin to make authenticated requests.

**New behavior:**
- CORS origins must be explicitly configured
- Supports multiple domains for development/staging/production
- Credentials support configurable

**Configuration:**

```bash
# Production - Restrict to your domains only
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Development - Include localhost for testing
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,https://yourdomain.com"

# Credentials (usually false for JWT bearer tokens)
export CORS_SUPPORTS_CREDENTIALS="false"
```

### 3. JWT Token Security

**What was fixed:** Long-lived tokens (30 days) with no revocation mechanism.

**New behavior:**
- Default token expiry: 15 minutes (configurable)
- Encourages implementing refresh token flow
- Configurable via environment variables

**Configuration:**

```bash
# Set token expiry in minutes
export JWT_EXPIRES_MINUTES="15"  # 15 minutes (recommended)
export JWT_EXPIRES_MINUTES="60"  # 1 hour (if needed)
```

### 4. Access Control Validation

**What was fixed:** Insecure Direct Object Reference allowing users to access other users' data.

**New behavior:**
- All template exercise references validated against user ownership
- Clear error messages for unauthorized access attempts
- Prevents cross-tenant data leakage

### 5. Production Security Enforcement

**What was fixed:** Debug mode could be accidentally enabled in production.

**New behavior:**
- Production config validates environment settings
- Prevents debug mode in production environments
- Clear error messages for misconfigurations

## 📋 Environment Variable Reference

### Required Variables (Production)

```bash
# Cryptographic secrets (32+ characters each)
SECRET_KEY="your-super-secret-key-here-minimum-32-characters-long"
JWT_SECRET_KEY="your-jwt-secret-key-here-minimum-32-characters-long"

# CORS security
CORS_ORIGINS="https://yourdomain.com"

# Environment
FLASK_ENV="production"
```

### Optional Variables

```bash
# JWT configuration
JWT_EXPIRES_MINUTES="15"                    # Token expiry (default: 15 minutes)

# CORS configuration
CORS_SUPPORTS_CREDENTIALS="false"           # Enable credentials (default: false)

# Database
DATABASE_PATH="/opt/workout-tracker/data/workout.db"  # Custom DB path

# Server
PORT="8080"                                 # Server port (default: 8080)
```

### Development Variables

```bash
# Skip secret validation in development only
SKIP_SECRET_VALIDATION="true"

# Development CORS (includes localhost)
CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080"
```

## 🐳 Docker Deployment

### Update your environment file

```bash
# Create .env file for docker-compose
cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CORS_ORIGINS=https://yourdomain.com
JWT_EXPIRES_MINUTES=15
CORS_SUPPORTS_CREDENTIALS=false
EOF

# Secure the file
chmod 600 .env
```

### Deploy with docker-compose

```bash
# The docker-compose.yml now uses environment variables without defaults
docker-compose up -d
```

## 🔒 Security Validation

### Test Configuration

```bash
# Test that default secrets are rejected
cd server
python3 -c "
import os
os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
from config import config
config['production']()
"
# Should exit with error

# Test valid configuration
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export CORS_ORIGINS="https://yourdomain.com"
python3 -c "from config import config; print('✅ Valid config'); config['production']()"
```

### Verify CORS Configuration

```bash
# Test CORS restrictions
curl -H "Origin: https://evil.com" http://localhost:8080/api/templates
# Should not include Access-Control-Allow-Origin header

curl -H "Origin: https://yourdomain.com" http://localhost:8080/api/templates  
# Should include Access-Control-Allow-Origin header
```

## 🚀 Deployment Checklist

### Before Production Deployment

- [ ] Generate secure secrets using `scripts/generate-secrets.py`
- [ ] Set `CORS_ORIGINS` to your actual domain(s)
- [ ] Set `FLASK_ENV=production`
- [ ] Verify secrets are at least 32 characters long
- [ ] Test that application starts without errors
- [ ] Verify CORS is working correctly
- [ ] Ensure `.env` file is not committed to git
- [ ] Set proper file permissions: `chmod 600 .env`

### Production Environment Variables

```bash
# Required for production
export SECRET_KEY="your-production-secret-key-32plus-chars"
export JWT_SECRET_KEY="your-production-jwt-secret-32plus-chars"
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
export FLASK_ENV="production"
export JWT_EXPIRES_MINUTES="15"
export DATABASE_PATH="/opt/workout-tracker/data/workout.db"
```

## 🔄 Secret Rotation

For production secret rotation:

```bash
# Generate new secrets
python3 scripts/generate-secrets.py

# Update environment variables
# Restart application
docker-compose restart workout-tracker
```

## ⚠️ Security Notes

1. **Never use default secrets in production**
2. **Keep CORS_ORIGINS restricted to your domains**
3. **Use HTTPS-only domains in production**
4. **Monitor for authentication failures**
5. **Rotate secrets regularly**
6. **Keep `.env` files secure and out of git**

### Known Security Considerations

**JWT Token Storage:** Currently using `localStorage` for JWT tokens, which is vulnerable to XSS attacks. Consider implementing:
- Refresh token flow with short-lived access tokens (current: 15 minutes)
- Content Security Policy (CSP) headers to prevent XSS
- Regular security scans for XSS vulnerabilities
- Future migration to `httpOnly` cookies with CSRF protection

## 🆘 Troubleshooting

### Application won't start

```bash
❌ SECURITY ERROR: SECRET_KEY not set or using default value!
```
**Solution:** Set a proper SECRET_KEY environment variable with 32+ characters.

### CORS errors in browser

```
Access to fetch at 'http://api.example.com' from origin 'https://app.example.com' has been blocked by CORS policy
```
**Solution:** Add your frontend domain to CORS_ORIGINS environment variable.

### JWT tokens expire too quickly

**Solution:** Increase JWT_EXPIRES_MINUTES or implement refresh token flow.

For more security questions, refer to the full security review report: `security-review-2025-01-27.md`
