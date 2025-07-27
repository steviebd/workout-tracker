from db import init_db
from models import User, Template, TemplateExercise
import secrets
import string
import os

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Try to load from project root first, then current directory
    env_loaded = False
    if os.path.exists('../.env'):
        load_dotenv('../.env', override=True)
        env_loaded = True
        print("📁 Loaded environment from ../.env")
    elif os.path.exists('.env'):
        load_dotenv('.env', override=True)
        env_loaded = True
        print("📁 Loaded environment from ./.env")
    
    if not env_loaded:
        print("⚠️  No .env file found, using system environment variables")
        
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    print("💡 Install with: pip install python-dotenv")

def generate_temp_password():
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(12))
    # Ensure it meets requirements
    password = 'A' + password[1:] if not any(c.isupper() for c in password) else password
    password = 'a' + password[1:] if not any(c.islower() for c in password) else password
    password = '1' + password[1:] if not any(c.isdigit() for c in password) else password
    password = '!' + password[1:] if not any(c in "!@#$%^&*" for c in password) else password
    return password

def seed_data():
    """Create sample data for testing."""
    # Debug environment and paths
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Script directory: {os.path.dirname(__file__)}")
    print(f"🌍 FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
    print(f"🌍 DATABASE_PATH env var: {os.environ.get('DATABASE_PATH', 'not set')}")
    
    # Debug database path
    from db import DB_PATH
    print(f"🗄️  Database path from db.py: {DB_PATH}")
    
    # Check if we're trying to use production path in development
    if DB_PATH.startswith('/opt/workout-tracker') and os.environ.get('FLASK_ENV') == 'development':
        print("⚠️  WARNING: Using production database path in development mode!")
        print("💡 This usually means the .env file wasn't loaded properly")
        # Use a safe development path instead
        safe_db_path = os.path.join(os.path.dirname(__file__), 'workout.db')
        print(f"🔄 Using safe development path instead: {safe_db_path}")
        os.environ['DATABASE_PATH'] = safe_db_path
        # Reload db module to pick up new path
        import importlib
        import db
        importlib.reload(db)
        from db import DB_PATH
    
    # Handle relative paths that might not resolve correctly
    if DB_PATH.startswith('./'):
        # Convert relative path to absolute path based on current working directory
        abs_db_path = os.path.abspath(DB_PATH)
        print(f"🔄 Converting relative path {DB_PATH} to absolute: {abs_db_path}")
        os.environ['DATABASE_PATH'] = abs_db_path
        # Reload db module to pick up new path
        import importlib
        import db
        importlib.reload(db)
        from db import DB_PATH
    
    # Ensure database directory exists (only for safe paths)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not db_dir.startswith('/opt/'):  # Safety check
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print(f"📁 Created database directory: {db_dir}")
            except PermissionError as e:
                print(f"❌ Permission denied creating directory: {db_dir}")
                print(f"💡 Try running with appropriate permissions or check your .env file")
                raise e
    elif db_dir.startswith('/opt/'):
        print("⚠️  Skipping directory creation for production path in development")
    
    init_db()
    
<<<<<<< HEAD
    # Create admin user - use password from env if available (from generate-secrets.py)
    admin_password = os.environ.get('ADMIN_TEMP_PASSWORD', generate_temp_password())
    admin_id = User.create('admin', admin_password, 'admin@example.com', 'admin', must_change_password=True)
    if admin_id:
        print(f"Created admin user with ID: {admin_id}")
        print(f"Admin username: admin")
        print(f"Admin temporary password: {admin_password}")
        print("IMPORTANT: The admin must change their password on first login!")
    
    # Create test user
    user_id = User.create('testuser', 'TestPassword123!', 'testuser@example.com')
=======
    # Create test user
user_id = User.create(
    username='testuser',
    email='test@example.com',
    password='TestPass123!',
    role='user'
)
    if user_id:
        print(f"Created test user with ID: {user_id}")
        
        # Create sample templates
        push_template_id = Template.create(user_id, 'Push Day')
        if push_template_id:
            TemplateExercise.create(push_template_id, 'Bench Press', 0)
            TemplateExercise.create(push_template_id, 'Overhead Press', 1)
            TemplateExercise.create(push_template_id, 'Push-ups', 2)
            print(f"Created Push Day template with exercises")
        
        pull_template_id = Template.create(user_id, 'Pull Day')
        if pull_template_id:
            TemplateExercise.create(pull_template_id, 'Pull-ups', 0)
            TemplateExercise.create(pull_template_id, 'Rows', 1)
            TemplateExercise.create(pull_template_id, 'Deadlift', 2)
            print(f"Created Pull Day template with exercises")

if __name__ == '__main__':
    seed_data()
