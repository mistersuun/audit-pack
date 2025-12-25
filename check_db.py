
from main import create_app
from database import db, Task

app = create_app()
with app.app_context():
    front_tasks = Task.query.filter_by(role='front').count()
    back_tasks = Task.query.filter_by(role='back').count()
    print(f"Front tasks: {front_tasks}")
    print(f"Back tasks: {back_tasks}")
    
    first_front = Task.query.filter_by(role='front').first()
    if first_front:
        print(f"First front task: {first_front.title_fr} ({first_front.category})")
