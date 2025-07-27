# Development Guide - Workout Tracker PWA

## Quick Start

### Backend Setup
1. **Install dependencies:**
   ```bash
   cd server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   python seed.py
   ```

3. **Start server:**
   ```bash
   python app.py
   ```

The server runs on `http://localhost:8080`

### Test Credentials
- **Username:** `testuser`
- **Password:** `password123`

## Development Environment

### Environment Variables
For development, you can skip security validation:
```bash
export SKIP_SECRET_VALIDATION="true"
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080"
```

### Frontend Development
The frontend is served by Flask as static files from the `public/` directory.

**Testing Files Available:**
- `test-settings.html` - Settings tab testing
- `simple-settings-test.html` - Simplified settings test
- `no-auth-index.html` - No authentication version for UI testing

### Development Commands
- **Start dev server:** `cd server && python app.py`
- **Initialize DB:** `cd server && python seed.py`
- **Reset database:** Delete `workout.db` and run `python seed.py`

## Architecture

### Backend (Flask)
- **Framework:** Flask with SQLite database
- **Authentication:** JWT with Flask-JWT-Extended
- **Database:** SQLite with foreign key constraints
- **Structure:**
  - `app.py` - Main Flask application and routes
  - `models.py` - Database models and business logic
  - `auth.py` - Authentication helpers
  - `db.py` - Database connection and utilities
  - `config.py` - Configuration and security validation

### Frontend (Vanilla JS PWA)
- **No frameworks** - Pure JavaScript and HTML
- **Styling:** Tailwind CSS (CDN)
- **Offline storage:** IndexedDB with Dexie.js
- **PWA features:** Service worker for offline capabilities
- **Structure:**
  - `public/index.html` - Main app interface
  - `public/app.js` - Application logic
  - `public/sw.js` - Service worker for offline functionality

### Database Schema
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  email TEXT,
  role TEXT DEFAULT 'user',
  must_change_password BOOLEAN DEFAULT FALSE
);

CREATE TABLE templates (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  UNIQUE(user_id, name)
);

CREATE TABLE template_exercises (
  id INTEGER PRIMARY KEY,
  template_id INTEGER REFERENCES templates(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  order_idx INTEGER NOT NULL
);

CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  template_id INTEGER REFERENCES templates(id) ON DELETE CASCADE,
  session_date TIMESTAMP NOT NULL
);

CREATE TABLE session_exercises (
  id INTEGER PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
  template_exercise_id INTEGER REFERENCES template_exercises(id) ON DELETE CASCADE,
  weight_kg REAL NOT NULL,
  reps INTEGER NOT NULL,
  sets INTEGER NOT NULL
);
```

## API Documentation

### Authentication
```bash
# Register
POST /api/auth/register
{
  "username": "newuser",
  "password": "newpassword"
}

# Login
POST /api/auth/login
{
  "username": "testuser",
  "password": "password123"
}

# Change password
PUT /api/auth/change-password
{
  "current_password": "oldpass",
  "new_password": "newpass"
}

# Forgot password
POST /api/auth/forgot-password
{
  "email": "user@example.com"
}

# Reset password
POST /api/auth/reset-password
{
  "token": "reset-token",
  "new_password": "newpass"
}
```

### Templates
```bash
# Get all templates
GET /api/templates
Authorization: Bearer <token>

# Create template
POST /api/templates
{
  "name": "Push Day",
  "exercises": ["Bench Press", "Push-ups"]
}

# Update template
PUT /api/templates/{id}
{
  "name": "Updated Push Day",
  "exercises": ["Bench Press", "Dips"]
}

# Delete template
DELETE /api/templates/{id}
```

### Sessions
```bash
# Get all sessions
GET /api/sessions
Authorization: Bearer <token>

# Create session
POST /api/sessions
{
  "template_id": 1,
  "session_date": "2024-01-15T10:30:00Z",
  "exercises": [
    {
      "template_exercise_id": 1,
      "weight_kg": 80.5,
      "reps": 8,
      "sets": 3
    }
  ]
}

# Delete session
DELETE /api/sessions/{id}
```

### Admin User Management
```bash
# List all users (admin only)
GET /api/admin/users
Authorization: Bearer <admin-token>

# Create user (admin only)
POST /api/admin/users
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "temppass",
  "role": "user"
}

# Update user (admin only)
PUT /api/admin/users/{id}
{
  "username": "updateduser",
  "email": "newemail@example.com",
  "role": "admin"
}

# Reset user password (admin only)
POST /api/admin/users/{id}/reset-password
{
  "new_password": "newtempass"
}

# Delete user (admin only)
DELETE /api/admin/users/{id}
```

## Code Style & Conventions

### Python (Backend)
- **Naming:** snake_case for variables, functions, modules
- **Imports:** Contextual imports (`from models import User`)
- **Database:** Use `get_db()` context manager
- **Error handling:** Return JSON with error messages
- **Security:** Always use parameterized SQL queries

### JavaScript (Frontend)
- **Naming:** camelCase for variables, PascalCase for classes
- **Async:** Use `async/await` for API calls
- **Storage:** Dexie for IndexedDB operations
- **Error handling:** Try/catch blocks with user-friendly messages

### File Structure
```
server/
├── app.py              # Main Flask application
├── models.py           # Database models
├── auth.py             # Authentication helpers
├── db.py               # Database utilities
├── config.py           # Configuration
├── validation.py       # Input validation
├── security_logger.py  # Security audit logging
└── requirements.txt    # Python dependencies

public/
├── index.html         # Main application
├── app.js            # JavaScript logic
├── sw.js             # Service worker
└── manifest.json     # PWA manifest
```

## Development Workflows

### Making Changes

1. **Backend changes:**
   - Modify files in `server/` directory
   - Restart with `python app.py`
   - Database schema changes: Delete `workout.db` and run `python seed.py`

2. **Frontend changes:**
   - Modify files in `public/` directory
   - Refresh browser (no build step required)

3. **Database changes:**
   - Update schema in `db.py`
   - Delete existing `workout.db`
   - Run `python seed.py` to recreate

### Testing

**No automated tests currently exist.** Tests should be added using:
- **Backend:** Python unittest or pytest
- **Frontend:** Manual testing or browser automation
- **API:** Postman collections or curl scripts

### Frontend Testing

The Settings tab can be tested with:
1. **Main app:** Settings should be accessible via navigation
2. **Test file:** Open `test-settings.html` for isolated testing
3. **Debug:** Check browser console for JavaScript errors

### Security Testing

```bash
# Test secret validation
cd server
SECRET_KEY="dev-secret-key" python3 -c "from config import config; config['production']()"
# Should fail with security error

# Test CORS
curl -H "Origin: https://evil.com" http://localhost:8080/api/templates
# Should not include CORS headers
```

## Debugging

### Common Issues

1. **Service won't start:**
   ```bash
   # Check environment variables
   env | grep -E "(SECRET_KEY|JWT_SECRET|CORS)"
   
   # Check database permissions
   ls -la workout.db
   ```

2. **Database errors:**
   ```bash
   # Recreate database
   rm workout.db
   python seed.py
   ```

3. **CORS errors:**
   ```bash
   # Check CORS_ORIGINS setting
   echo $CORS_ORIGINS
   
   # For development, set to localhost
   export CORS_ORIGINS="http://localhost:8080"
   ```

4. **JWT errors:**
   ```bash
   # Check token expiry setting
   echo $JWT_EXPIRES_MINUTES
   
   # Default is 15 minutes
   export JWT_EXPIRES_MINUTES="60"  # 1 hour for development
   ```

### Logging

- **Application logs:** Console output when running `python app.py`
- **Security logs:** `logs/security.log` (JSON format)
- **Error logs:** Check console for Python tracebacks

### Database Debugging

```bash
# Inspect database directly
sqlite3 workout.db

# Useful queries
.schema
SELECT * FROM users;
SELECT * FROM templates WHERE user_id = 1;
```

## Performance Considerations

### Database
- SQLite is suitable for single-user/small team use
- For production with multiple users, consider PostgreSQL
- Connection per request (no pooling) - fine for current scale

### Frontend
- Service worker caches static assets
- IndexedDB stores data offline
- Tailwind CSS loaded from CDN (consider local copy for production)

### Rate Limiting
- Default: 1000 requests/hour, 100/minute for general API
- Authentication: 5 login attempts/minute, 3 registrations/minute
- Adjust via environment variables for development

## Contributing

### Before Making Changes
1. Test locally with `python app.py`
2. Verify security features work
3. Check that authentication flow works
4. Test offline capabilities

### Code Quality
- Follow existing code style
- Add error handling for new features
- Use parameterized queries for database operations
- Validate all user inputs
- Test edge cases

### Security Considerations
- Never hardcode secrets
- Always validate user ownership of data
- Use proper HTTP status codes
- Log security-relevant events
- Test authentication boundaries

This development guide should help you understand the codebase structure and development workflow for the Workout Tracker PWA.
