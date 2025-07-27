from db import init_db
from models import User, Template, TemplateExercise

def seed_data():
    """Create sample data for testing."""
    init_db()
    
    # Create test user
    user_id = User.create('testuser', 'TestPassword123!')
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
