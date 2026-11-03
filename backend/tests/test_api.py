from datetime import date


def employee_payload(email="ava@example.com"):
    return {"full_name": "Ava Patel", "email": email, "department": "Engineering", "job_title": "Developer", "joining_date": "2024-01-15", "is_active": True}


def project_payload(manager_id=None):
    return {"name": "Atlas", "description": "Platform refresh", "manager_id": manager_id, "start_date": "2025-01-01", "end_date": "2025-06-01", "status": "In Progress", "progress": 40}


def task_payload(project_id, employee_id=None):
    return {"title": "Build overview", "description": "", "project_id": project_id, "employee_id": employee_id, "priority": "High", "status": "Open", "due_date": "2025-04-01"}


def test_health(client):
    assert client.get('/api/health').json()['status'] == 'ok'


def test_employee_crud_and_duplicate(client):
    r = client.post('/api/employees', json=employee_payload()); assert r.status_code == 201
    ident = r.json()['id']
    assert client.get(f'/api/employees/{ident}').json()['email'] == 'ava@example.com'
    assert client.post('/api/employees', json=employee_payload()).status_code == 409
    updated = employee_payload(); updated['job_title'] = 'Senior Developer'
    assert client.put(f'/api/employees/{ident}', json=updated).json()['job_title'] == 'Senior Developer'
    assert client.delete(f'/api/employees/{ident}').status_code == 204
    assert client.get(f'/api/employees/{ident}').status_code == 404


def test_project_crud(client):
    employee = client.post('/api/employees', json=employee_payload()).json()
    r = client.post('/api/projects', json=project_payload(employee['id'])); assert r.status_code == 201
    ident = r.json()['id']; assert r.json()['manager_name'] == 'Ava Patel'
    payload = project_payload(employee['id']); payload['progress'] = 75
    assert client.put(f'/api/projects/{ident}', json=payload).json()['progress'] == 75
    assert client.delete(f'/api/projects/{ident}').status_code == 204
    assert client.get(f'/api/projects/{ident}').status_code == 404


def test_task_crud_and_reference_validation(client):
    project = client.post('/api/projects', json=project_payload()).json()
    employee = client.post('/api/employees', json=employee_payload()).json()
    r = client.post('/api/tasks', json=task_payload(project['id'], employee['id'])); assert r.status_code == 201
    ident = r.json()['id']; assert r.json()['employee_name'] == 'Ava Patel'
    payload = task_payload(project['id'], employee['id']); payload['status'] = 'Completed'
    assert client.put(f'/api/tasks/{ident}', json=payload).json()['status'] == 'Completed'
    assert client.post('/api/tasks', json=task_payload(999)).status_code == 400
    assert client.post('/api/tasks', json=task_payload(project['id'], 999)).status_code == 400
    assert client.delete(f'/api/tasks/{ident}').status_code == 204
    assert client.get(f'/api/tasks/{ident}').status_code == 404


def test_invalid_data_and_dashboard_stats(client):
    assert client.post('/api/employees', json={**employee_payload(), 'email': 'not-an-email'}).status_code == 422
    assert client.post('/api/employees', json=employee_payload()).status_code == 201
    project = client.post('/api/projects', json=project_payload()).json()
    client.post('/api/tasks', json=task_payload(project['id']))
    client.post('/api/tasks', json={**task_payload(project['id']), 'status': 'Completed'})
    stats = client.get('/api/dashboard/stats').json()
    assert stats['total_employees'] == 1 and stats['total_projects'] == 1
    assert stats['open_tasks'] == 1 and stats['completed_tasks'] == 1
