# Workout Tracker PWA - Agent Guidelines

## Commands
- **Start dev server**: `cd server && python app.py` (Flask app on :8080)
- **Initialize DB**: `cd server && python seed.py`
- **Install backend**: `cd server && pip install -r requirements.txt`
- **Production**: `docker-compose up -d` or use deployment scripts
- **No tests found** - Tests should be added using standard Python unittest/pytest patterns

## Architecture
- **Backend**: Flask API (`server/`) with SQLite database, JWT auth
- **Frontend**: Vanilla JS PWA (`public/`) with Tailwind CSS, IndexedDB offline storage
- **Database**: SQLite with users, templates, template_exercises, sessions, session_exercises
- **Production**: Docker + nginx reverse proxy, Cloudflare tunnels

## Code Style
- **Python**: Snake_case, contextual imports (`from models import User`), use `get_db()` context manager
- **JavaScript**: CamelCase classes, `async/await` for API calls, Dexie for IndexedDB
- **API**: RESTful endpoints under `/api/`, JWT Bearer token auth required
- **Errors**: Return JSON with error messages, use try/catch blocks
- **Security**: Parameterized SQL queries, password hashing with Werkzeug, JWT tokens
- **File structure**: Models in `models.py`, routes in `app.py`, DB helpers in `db.py`
