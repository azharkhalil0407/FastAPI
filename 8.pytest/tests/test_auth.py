def test_register_success(client):
    response = client.post("/users/register", json={
        "email": "test@example.com",
        "password": "secret123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["is_active"] == True

def test_login_success(client):
    client.post("/users/register", json={
        "email": "logintest@example.com",
        "password": "mypassword"
    })
    response = client.post("/users/login", data={
        "username": "logintest@example.com",
        "password": "mypassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post("/users/register", json={
        "email": "wrongpass@example.com",
        "password": "correct123"
    })
    response = client.post("/users/login", data={
        "username": "wrongpass@example.com",
        "password": "wrong123"
    })
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid credentials"

def test_get_me_success(client):
    client.post("/users/register", json={
        "email": "me@example.com",
        "password": "me123"
    })
    login_res = client.post("/users/login", data={
        "username": "me@example.com",
        "password": "me123"
    })
    token = login_res.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"

def test_get_me_unauthorized(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_get_me_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer galat_token"})
    assert response.status_code == 401