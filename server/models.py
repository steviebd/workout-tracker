from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
import sqlite3
import re
import os
from datetime import datetime

class User:
    @staticmethod
    def get_password_policy():
        """Get password policy from configuration."""
        from config import config
        config_name = os.environ.get('FLASK_ENV', 'development')
        
        # Get config instance to access password policy
        if config_name in config:
            config_obj = config[config_name]()
            return {
                'min_length': config_obj.PASSWORD_MIN_LENGTH,
                'max_length': config_obj.PASSWORD_MAX_LENGTH,
                'require_uppercase': config_obj.PASSWORD_REQUIRE_UPPERCASE,
                'require_lowercase': config_obj.PASSWORD_REQUIRE_LOWERCASE,
                'require_numbers': config_obj.PASSWORD_REQUIRE_NUMBERS,
                'require_special': config_obj.PASSWORD_REQUIRE_SPECIAL,
                'block_common': config_obj.PASSWORD_BLOCK_COMMON,
            }
        else:
            # Fallback defaults
            return {
                'min_length': 8,
                'max_length': 128,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special': True,
                'block_common': True,
            }
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength according to configurable security policy.
        Returns (is_valid, error_message)
        """
        policy = User.get_password_policy()
        
        if len(password) < policy['min_length']:
            return False, f"Password must be at least {policy['min_length']} characters long"
        
        if len(password) > policy['max_length']:
            return False, f"Password must be no longer than {policy['max_length']} characters"
        
        requirements = []
        
        # Check for lowercase letter
        if policy['require_lowercase'] and not re.search(r'[a-z]', password):
            requirements.append("one lowercase letter")
        
        # Check for uppercase letter
        if policy['require_uppercase'] and not re.search(r'[A-Z]', password):
            requirements.append("one uppercase letter")
        
        # Check for digit
        if policy['require_numbers'] and not re.search(r'\d', password):
            requirements.append("one number")
        
        # Check for special character
        if policy['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            requirements.append("one special character (!@#$%^&*(),.?\":{}|<>)")
        
        if requirements:
            return False, f"Password must contain at least: {', '.join(requirements)}"
        
        # Check for common weak passwords
        if policy['block_common']:
            weak_passwords = [
                'password', 'password123', '12345678', 'qwerty123', 'admin123',
                'letmein', 'welcome123', 'monkey123', '123456789', 'password1',
                '123456', 'admin', 'guest', 'test', 'user'
            ]
            if password.lower() in weak_passwords:
                return False, "Password is too common and easily guessable"
        
        return True, "Password meets security requirements"
    
    @staticmethod
    def create(username, password):
        # Validate password strength
        is_valid, error_message = User.validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_message)
        
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
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Change user password after verifying current password.
        Returns (success, error_message)
        """
        # Get user by ID
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not check_password_hash(user['password_hash'], current_password):
                return False, "Current password is incorrect"
            
            # Validate new password strength
            is_valid, error_message = User.validate_password_strength(new_password)
            if not is_valid:
                return False, error_message
            
            # Check that new password is different from current
            if check_password_hash(user['password_hash'], new_password):
                return False, "New password must be different from current password"
            
            # Update password
            new_password_hash = generate_password_hash(new_password)
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user_id)
            )
            conn.commit()
            
            return True, "Password changed successfully"

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
