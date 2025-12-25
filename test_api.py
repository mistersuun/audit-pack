
import requests
from main import create_app

def test_api():
    app = create_app()
    client = app.test_client()

    # Login
    with client.session_transaction() as sess:
        sess['authenticated'] = True
    
    # 1. Test Default (Front)
    # Set role
    client.post('/api/set-role', json={'role': 'front'})
    
    # Get Tasks
    response = client.get('/api/tasks')
    tasks = response.get_json()
    print(f"Front Tasks Count: {len(tasks)}")
    if len(tasks) > 0:
        print(f"Sample Front Task: {tasks[0]['title_fr']} (Category: {tasks[0]['category']})")

    # 2. Test Back
    client.post('/api/set-role', json={'role': 'back'})
    response = client.get('/api/tasks')
    tasks = response.get_json()
    print(f"Back Tasks Count: {len(tasks)}")
    if len(tasks) > 0:
        print(f"Sample Back Task: {tasks[0]['title_fr']} (Category: {tasks[0]['category']})")

if __name__ == "__main__":
    test_api()
