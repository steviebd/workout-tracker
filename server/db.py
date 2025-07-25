import sqlite3
import os
from contextlib import contextmanager

# Use environment variable for database path in production
DB_PATH = os.environ.get('DATABASE_PATH') or os.path.join(os.path.dirname(__file__), 'workout.db')

def init_db():
    """Initialize the database with the required schema."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                UNIQUE(user_id, name)
            );

            CREATE TABLE IF NOT EXISTS template_exercises (
                id INTEGER PRIMARY KEY,
                template_id INTEGER REFERENCES templates(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                order_idx INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                template_id INTEGER REFERENCES templates(id) ON DELETE CASCADE,
                session_date TIMESTAMP NOT NULL
            );

            CREATE TABLE IF NOT EXISTS session_exercises (
                id INTEGER PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                template_exercise_id INTEGER REFERENCES template_exercises(id) ON DELETE CASCADE,
                weight_kg REAL NOT NULL,
                reps INTEGER NOT NULL,
                sets INTEGER NOT NULL
            );
        """)

@contextmanager
def get_db():
    """Get a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
