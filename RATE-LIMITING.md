# Rate Limiting Configuration

The Workout Tracker PWA includes configurable rate limiting to protect against abuse and ensure service availability.

## 🚦 Environment Variables

All rate limiting settings are configurable via environment variables:

### General API Limits
```bash
# Default rate limits for all API endpoints
RATE_LIMIT_DEFAULT="1000 per hour, 100 per minute"
```

### Authentication Endpoints
```bash
# Login endpoint rate limit
RATE_LIMIT_AUTH_LOGIN="5 per minute"

# Registration endpoint rate limit  
RATE_LIMIT_AUTH_REGISTER="3 per minute"
```

### Storage Configuration
```bash
# Rate limiting storage backend
RATE_LIMIT_STORAGE_URI="memory://"           # Single instance (default)
RATE_LIMIT_STORAGE_URI="redis://localhost:6379"  # Distributed/clustered
```

## 📊 Default Values

### Production Environment
- **General API**: 1000 requests/hour, 100 requests/minute
- **Login**: 5 attempts/minute
- **Registration**: 3 attempts/minute
- **Storage**: In-memory

### Development Environment  
- **General API**: 2000 requests/hour, 200 requests/minute
- **Login**: 10 attempts/minute
- **Registration**: 5 attempts/minute
- **Storage**: In-memory

## 🔧 Configuration Examples

### Strict Production Setup
```bash
export RATE_LIMIT_DEFAULT="500 per hour, 50 per minute"
export RATE_LIMIT_AUTH_LOGIN="3 per minute"
export RATE_LIMIT_AUTH_REGISTER="2 per minute"
```

### High-Traffic Setup
```bash
export RATE_LIMIT_DEFAULT="5000 per hour, 300 per minute"
export RATE_LIMIT_AUTH_LOGIN="20 per minute"
export RATE_LIMIT_AUTH_REGISTER="10 per minute"
```

### Redis-backed Distributed Setup
```bash
export RATE_LIMIT_STORAGE_URI="redis://redis-cluster:6379"
export RATE_LIMIT_DEFAULT="2000 per hour, 150 per minute"
```

## 🛡️ Security Considerations

### Rate Limit Format
- **Single limit**: `"100 per minute"` or `"1000 per hour"`
- **Multiple limits**: `"1000 per hour, 100 per minute"` (comma-separated)
- **Time units**: `per second`, `per minute`, `per hour`, `per day`

### Recommendations
1. **Production**: Use stricter limits than development
2. **Authentication**: Keep auth endpoints heavily restricted
3. **Monitoring**: Monitor rate limit hits in security logs
4. **Redis**: Use Redis for multi-instance deployments
5. **Tuning**: Adjust based on legitimate usage patterns

## 📝 Rate Limit Responses

When limits are exceeded, the API returns:
```json
{
  "message": "Rate limit exceeded",
  "status": 429
}
```

## 🔍 Monitoring

Rate limit events are logged in the security audit log:
```json
{
  "event_type": "RATE_LIMIT_EXCEEDED",
  "limit_type": "auth_login",
  "ip_address": "192.168.1.100",
  "timestamp": "2025-01-27T12:00:00Z"
}
```

## 🚀 Deployment

### Docker Compose
Rate limiting variables are automatically configured in `docker-compose.yml` with secure defaults.

### Manual Deployment
Set environment variables before starting the application:
```bash
export RATE_LIMIT_AUTH_LOGIN="5 per minute"
python server/app.py
```

### Configuration Script
Use the interactive configuration generator:
```bash
python3 scripts/generate-secrets.py
```

This will prompt for rate limiting preferences and generate appropriate environment variables.
