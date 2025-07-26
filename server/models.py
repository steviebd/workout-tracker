from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
import sqlite3
from datetime import datetime

class User:
    @staticmethod
    def create(username, password):
        password_hash = generate_password_hash(password)
        with get_db() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    @staticmethod
    def get_by_username(username):
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            return dict(user) if user else None

    @staticmethod
    def verify_password(username, password):
        user = User.get_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

class Template:
    @staticmethod
    def create(user_id, name):
        with get_db() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO templates (user_id, name) VALUES (?, ?)",
                    (user_id, name)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    @staticmethod
    def get_all_by_user(user_id):
        with get_db() as conn:
            templates = conn.execute(
                "SELECT * FROM templates WHERE user_id = ? ORDER BY name",
                (user_id,)
            ).fetchall()
            return [dict(t) for t in templates]

    @staticmethod
    def get_by_id(template_id, user_id):
        with get_db() as conn:
            template = conn.execute(
                "SELECT * FROM templates WHERE id = ? AND user_id = ?",
                (template_id, user_id)
            ).fetchone()
            return dict(template) if template else None

    @staticmethod
    def update(template_id, user_id, name):
        with get_db() as conn:
            cursor = conn.execute(
                "UPDATE templates SET name = ? WHERE id = ? AND user_id = ?",
                (name, template_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete(template_id, user_id):
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM templates WHERE id = ? AND user_id = ?",
                (template_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

class TemplateExercise:
    @staticmethod
    def create(template_id, name, order_idx):
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO template_exercises (template_id, name, order_idx) VALUES (?, ?, ?)",
                (template_id, name, order_idx)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_by_template(template_id):
        with get_db() as conn:
            exercises = conn.execute(
                "SELECT * FROM template_exercises WHERE template_id = ? ORDER BY order_idx",
                (template_id,)
            ).fetchall()
            return [dict(e) for e in exercises]

    @staticmethod
    def delete_by_template(template_id):
        with get_db() as conn:
            conn.execute("DELETE FROM template_exercises WHERE template_id = ?", (template_id,))
            conn.commit()
    
    @staticmethod
    def validate_ownership(template_exercise_id, user_id):
        """Validate that a template exercise belongs to the given user."""
        with get_db() as conn:
            result = conn.execute("""
                SELECT te.id 
                FROM template_exercises te
                JOIN templates t ON te.template_id = t.id
                WHERE te.id = ? AND t.user_id = ?
            """, (template_exercise_id, user_id)).fetchone()
            return result is not None
    
    @staticmethod
    def get_by_id(template_exercise_id):
        """Get a template exercise by ID."""
        with get_db() as conn:
            exercise = conn.execute(
                "SELECT * FROM template_exercises WHERE id = ?",
                (template_exercise_id,)
            ).fetchone()
            return dict(exercise) if exercise else None

class Session:
    @staticmethod
    def create(user_id, template_id, session_date=None):
        if session_date is None:
            session_date = datetime.utcnow().isoformat()
        
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (user_id, template_id, session_date) VALUES (?, ?, ?)",
                (user_id, template_id, session_date)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_by_user(user_id, template_id=None):
        with get_db() as conn:
            if template_id:
                sessions = conn.execute("""
                    SELECT s.*, t.name as template_name 
                    FROM sessions s 
                    JOIN templates t ON s.template_id = t.id 
                    WHERE s.user_id = ? AND s.template_id = ? 
                    ORDER BY s.session_date DESC
                """, (user_id, template_id)).fetchall()
            else:
                sessions = conn.execute("""
                    SELECT s.*, t.name as template_name 
                    FROM sessions s 
                    JOIN templates t ON s.template_id = t.id 
                    WHERE s.user_id = ? 
                    ORDER BY s.session_date DESC
                """, (user_id,)).fetchall()
            return [dict(s) for s in sessions]

    @staticmethod
    def delete(session_id, user_id):
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

class SessionExercise:
    @staticmethod
    def create(session_id, template_exercise_id, weight_kg, reps, sets):
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO session_exercises (session_id, template_exercise_id, weight_kg, reps, sets) VALUES (?, ?, ?, ?, ?)",
                (session_id, template_exercise_id, weight_kg, reps, sets)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_latest_by_template_exercise(template_exercise_id, user_id):
        with get_db() as conn:
            result = conn.execute("""
                SELECT se.weight_kg, se.reps, se.sets 
                FROM session_exercises se
                JOIN sessions s ON se.session_id = s.id
                WHERE se.template_exercise_id = ? AND s.user_id = ?
                ORDER BY s.session_date DESC
                LIMIT 1
            """, (template_exercise_id, user_id)).fetchone()
            return dict(result) if result else None

    @staticmethod
    def get_by_session(session_id):
        with get_db() as conn:
            exercises = conn.execute("""
                SELECT se.*, te.name as exercise_name 
                FROM session_exercises se
                JOIN template_exercises te ON se.template_exercise_id = te.id
                WHERE se.session_id = ?
                ORDER BY te.order_idx
            """, (session_id,)).fetchall()
            return [dict(e) for e in exercises]
