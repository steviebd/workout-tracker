# Workout Tracker PWA

A minimal, mobile-first Progressive Web App for tracking daily workouts using reusable templates with offline capabilities.

## Features

- 🏋️ **Template-based workouts** - Create reusable workout templates with custom exercises
- 📱 **Mobile-first PWA** - Optimized for mobile devices with app-like experience
- 🔐 **JWT Authentication** - Secure token-based authentication with role management
- 👥 **Flexible user management** - Built-in registration and admin-managed accounts
- 🔄 **Offline sync** - Works offline and syncs when back online
- 📊 **Workout history** - Track all your sessions with filtering
- ⚡ **Pre-filled values** - Last recorded weights/reps automatically populate
- 🛡️ **Role-based access** - User and admin roles with different permissions

## Quick Start

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Initialize database and seed data:**
   ```bash
   python seed.py
   ```

3. **Start the Flask server:**
   ```bash
   python app.py
   ```

The server will run on `http://localhost:8080`

### Frontend

The frontend is served by Flask as static files. Open `http://localhost:8080` in your browser.

### Test Credentials

Access the application at `http://localhost:8080` and login with:

- **Admin User:** `admin` / `[password generated during seed.py]` (has access to admin panel)
- **Registration:** Users can register directly at `/register`

⚠️ **Important:** Change the default admin password immediately after first login!

## API Endpoints

### Authentication

**Register a new user:**
```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "user@example.com", "password": "securepassword"}'
```

**Login and get JWT token:**
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'
```

**Get current user info:**
```bash
curl -X GET http://localhost:8080/api/user \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Admin - Get all users:**
```bash
curl -X GET http://localhost:8080/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN"
```

### Templates

**Get all templates:**
```bash
curl -X GET http://localhost:8080/api/templates \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Create a template:**
```bash
curl -X POST http://localhost:8080/api/templates \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Push Day", "exercises": ["Bench Press", "Overhead Press", "Push-ups"]}'
```

**Update a template:**
```bash
curl -X PUT http://localhost:8080/api/templates/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Push Day Updated", "exercises": ["Bench Press", "Overhead Press", "Dips"]}'
```

**Delete a template:**
```bash
curl -X DELETE http://localhost:8080/api/templates/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get template exercises:**
```bash
curl -X GET http://localhost:8080/api/templates/1/exercises \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Add exercise to template:**
```bash
curl -X POST http://localhost:8080/api/templates/1/exercises \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Exercise"}'
```

### Sessions

**Get last recorded values for an exercise:**
```bash
curl -X GET http://localhost:8080/api/sessions/latest/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Create a workout session:**
```bash
curl -X POST http://localhost:8080/api/sessions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "session_date": "2024-01-15T10:30:00Z",
    "exercises": [
      {"template_exercise_id": 1, "weight_kg": 80.5, "reps": 8, "sets": 3},
      {"template_exercise_id": 2, "weight_kg": 45.0, "reps": 10, "sets": 3}
    ]
  }'
```

**Get all sessions:**
```bash
curl -X GET http://localhost:8080/api/sessions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get sessions filtered by template:**
```bash
curl -X GET http://localhost:8080/api/sessions?template=1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Delete a session:**
```bash
curl -X DELETE http://localhost:8080/api/sessions/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Database Schema

The SQLite database uses the following schema:

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL
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

## PWA Features

- **Offline functionality** - Service worker caches static assets and queues API requests
- **Background sync** - Automatically syncs data when connection is restored
- **App-like experience** - Can be installed on mobile devices
- **Responsive design** - Works on all screen sizes with mobile-first approach

## Technology Stack

### Backend
- **Flask** - Python web framework
- **Flask-JWT-Extended** - JWT authentication
- **SQLite** - Database
- **Werkzeug** - Password hashing

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **Tailwind CSS** - Utility-first CSS framework (CDN)
- **Dexie** - IndexedDB wrapper for offline storage
- **Service Worker** - Offline capabilities with Workbox

## Production Deployment

For production deployment on LXC containers with Proxmox and Cloudflare Tunnels, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Production Setup

1. **Automated Installation:**
   ```bash
   chmod +x deployment/scripts/install.sh
   sudo ./deployment/scripts/install.sh
   ```

2. **Configure Environment:**
   ```bash
   sudo nano /opt/workout-tracker/.env
   # Set production values for SECRET_KEY, JWT_SECRET_KEY, etc.
   ```

3. **Set up Cloudflare Tunnel:**
   ```bash
   sudo ./deployment/cloudflare/setup-tunnel.sh
   ```

### Alternative Deployment Methods

- **Docker:** `docker-compose up -d`
- **LXC on Proxmox:** See detailed guide in DEPLOYMENT.md
- **Traditional VPS:** Use the install script on any Ubuntu/Debian server

## Development

To make changes:

1. **Backend changes:** Modify files in the `server/` directory and restart `python app.py`
2. **Frontend changes:** Modify files in the `public/` directory and refresh the browser
3. **Database changes:** Modify `db.py` and delete `workout.db` to recreate with new schema

## Security Features

### Production Security
- ✅ **Environment-based configuration** - Secure secrets management
- ✅ **JWT token authentication** - 30-day expiry by default
- ✅ **CORS protection** - Configured for production domains
- ✅ **SQL injection protection** - Parameterized queries
- ✅ **XSS protection** - Security headers via nginx
- ✅ **HTTPS ready** - SSL/TLS with Let's Encrypt or Cloudflare
- ✅ **User isolation** - Each user's data is completely isolated
- ✅ **Rate limiting** - API rate limiting via nginx
- ✅ **Fail2ban integration** - Automated IP blocking for abuse

### Security Best Practices
- Change default JWT/secret keys in production
- Use HTTPS in production (automatically handled with Cloudflare Tunnels)
- Regular security updates via automated scripts
- Database backups with encryption
- Log monitoring and alerting

## Offline Storage

The app uses IndexedDB to store:
- Templates and exercises for offline viewing
- Workout sessions when offline (synced when online)
- Pending API requests for background sync

Data is automatically synced when the device comes back online.

## Monitoring and Maintenance

### Built-in Features
- ✅ **Health check endpoint** - `/health`
- ✅ **Automated backups** - Daily database backups with 30-day retention
- ✅ **Log rotation** - Automated log management
- ✅ **System monitoring** - Resource usage tracking
- ✅ **Service monitoring** - Systemd integration with auto-restart

### Backup and Recovery
- Automated daily database backups
- Full system backup scripts
- One-click recovery procedures
- Backup verification and testing
