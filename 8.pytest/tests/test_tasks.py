def test_create_task_success(client, auth_headers):
    response = client.post("/tasks/", json={
        "title": "Buy groceries",
        "description": "Milk, eggs, bread"
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert "id" in data

def test_get_tasks_success(client, auth_headers):
    client.post("/tasks/", json={"title": "Task 1"}, headers=auth_headers)
    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1
    assert data["results"][0]["title"] == "Task 1"

def test_update_task_owner_success(client, auth_headers):
    create_res = client.post("/tasks/", json={"title": "Old title"}, headers=auth_headers)
    task_id = create_res.json()["id"]
    update_res = client.put(f"/tasks/{task_id}", json={"title": "New title"}, headers=auth_headers)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "New title"

def test_delete_task_owner_success(client, auth_headers):
    create_res = client.post("/tasks/", json={"title": "To delete"}, headers=auth_headers)
    task_id = create_res.json()["id"]
    delete_res = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert delete_res.status_code == 200
    get_res = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 404

def test_update_task_not_owner_fails(client):
    client.post("/users/register", json={"email": "owner@example.com", "password": "pass"})
    login_a = client.post("/users/login", data={"username": "owner@example.com", "password": "pass"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    create_res = client.post("/tasks/", json={"title": "Secret"}, headers=headers_a)
    task_id = create_res.json()["id"]
    client.post("/users/register", json={"email": "attacker@example.com", "password": "pass"})
    login_b = client.post("/users/login", data={"username": "attacker@example.com", "password": "pass"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    update_res = client.put(f"/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_b)
    assert update_res.status_code == 403