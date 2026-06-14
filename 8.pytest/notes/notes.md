# Testing FastAPI Applications

---

## Why Testing?

You manually tested your API via `/docs` — register, login, task create, everything worked. So why do you need automated tests?

Say tomorrow you add a new feature — "task due date". You change a few lines in `tasks.py`. By mistake, some `if` condition logic breaks elsewhere. You manually check once, twice — but in production a user can't create a task. Your reputation takes a hit.

Automated tests solve this. You write them once. After every change, a single command tells you whether everything still works or something broke. This is what makes you professional.

A test is a robot that gives your API different inputs and verifies the output. It follows the same steps every time — no laziness, no forgetting.

---

## pytest and TestClient Basic Setup

You don't want to run a real server for tests — it's slow and managing ports is a pain. `TestClient` is FastAPI's dummy HTTP client. It doesn't use a real network; it calls your app directly.

`TestClient(app)` creates an object where you can call `.get()`, `.post()`, `.put()`, `.delete()`. Internally it uses Starlette's request-like interface but doesn't open an actual socket.

First attempt — without fixtures:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register():
    response = client.post("/users/register", json={"email": "a@b.com", "password": "123"})
    assert response.status_code == 200
```

Problem: this uses the real PostgreSQL database, which doesn't clean itself. Run it twice and you get "Email already registered". This is why we need a temporary test database.

---

## Temporary Database and conftest.py

**The problem:** a test inserts `test@example.com` into the real database. Run the test again — duplicate email error. Manually cleaning after every run is not viable.

**The solution:** a fresh database for every test that disappears when the test is done. SQLite `:memory:` had an issue — every connection gets a separate database with no shared state. File-based `sqlite:///./test.db` works correctly.

**Why `conftest.py` matters:**

`conftest.py` is a special pytest file. Whatever fixtures you define inside it are automatically available to all test files in the same directory — no imports needed.

**What is a fixture?**

A fixture is a function decorated with `@pytest.fixture`. It creates some resource (a database session, an API client, a token) before the test runs and injects it into the test function.

**Fixtures we created:**

- `db_session` — creates a new SQLite engine, creates tables, yields a session, drops everything after the test.
- `client` — takes `db_session`, overrides FastAPI's `get_db` dependency, returns a `TestClient`.
- `registered_user` — registers a default user (`fixtureuser@example.com`).
- `auth_token` — logs in with that registered user and returns the token.
- `auth_headers` — puts the token into an `Authorization` header dict ready to use.

**Understanding dependency override:**

FastAPI has a `get_db` function that returns a real database session. In tests, we want `get_db` to return our test session instead. So we do `app.dependency_overrides[get_db] = override_get_db`. This replaces the database inside FastAPI without touching any original application code.

**Final `conftest.py`:**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.database import Base, get_db
from app.models.users import User
from app.models.tasks import Task
from app.models.tags import Tag, task_tags

TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def registered_user(client):
    email = "fixtureuser@example.com"
    password = "fixturepass"
    client.post("/users/register", json={"email": email, "password": password})
    return {"email": email, "password": password}

@pytest.fixture(scope="function")
def auth_token(client, registered_user):
    response = client.post("/users/login", data={
        "username": registered_user["email"],
        "password": registered_user["password"]
    })
    return response.json()["access_token"]

@pytest.fixture(scope="function")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
```

`scope="function"` means a fresh database, fresh client, and fresh user for every single test. Tests stay completely independent of each other.

---

## Auth Endpoint Tests (`test_auth.py`)

Register, login, and `/me` are the most basic security features. Without them no protected route should be accessible.

**What these tests verify:**
- Register success returns `200` with `email`, `id`, `is_active`.
- Login success returns `access_token`.
- Wrong password returns `401`.
- Calling `/me` without a token returns `401`.
- Invalid token returns `401`.

**Note on test design:** auth tests register with unique emails per test rather than reusing the `registered_user` fixture, because that fixture already claims `fixtureuser@example.com`. Reusing that email in `test_register_success` would fail with a duplicate email error.

```python
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
    client.post("/users/register", json={"email": "logintest@example.com", "password": "mypassword"})
    response = client.post("/users/login", data={
        "username": "logintest@example.com",
        "password": "mypassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post("/users/register", json={"email": "wrongpass@example.com", "password": "correct123"})
    response = client.post("/users/login", data={
        "username": "wrongpass@example.com",
        "password": "wrong123"
    })
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid credentials"

def test_get_me_success(client):
    client.post("/users/register", json={"email": "me@example.com", "password": "me123"})
    login_res = client.post("/users/login", data={"username": "me@example.com", "password": "me123"})
    token = login_res.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"

def test_get_me_unauthorized(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_get_me_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer bad_token"})
    assert response.status_code == 401
```

---

## CRUD Task Tests (`test_tasks.py`)

Create, read, update, delete is the core functionality. On top of that, permission checks must ensure only the owner can update or delete their own task.

**Problems encountered and how they were solved:**
- `owner_id` missing from response — the response model didn't include it, so that assertion was removed.
- `GET /tasks/` returns a paginated dict, not a plain list — used `data["results"]` in the test.
- `DELETE` returns `200` instead of `204` — the route didn't declare `status_code=204`, so the assertion was updated to check for `200`.
- Permission test — created two separate users and verified the second user cannot update the first user's task.

```python
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
    # User A creates a task
    client.post("/users/register", json={"email": "owner@example.com", "password": "pass"})
    login_a = client.post("/users/login", data={"username": "owner@example.com", "password": "pass"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    create_res = client.post("/tasks/", json={"title": "Secret"}, headers=headers_a)
    task_id = create_res.json()["id"]

    # User B tries to update it
    client.post("/users/register", json={"email": "attacker@example.com", "password": "pass"})
    login_b = client.post("/users/login", data={"username": "attacker@example.com", "password": "pass"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    update_res = client.put(f"/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_b)
    assert update_res.status_code == 403
```

---

## Real Problems Encountered and Solutions

**`ModuleNotFoundError` for `fastapi` despite installing**

Cause: virtual environment was active but packages were installed at system level. `pip3` was installing globally.

Fix: always install after running `source venv/bin/activate`.

---

**Circular import in `database.py`**

Error: `from app.database import sessionLocal` inside `database.py` itself.

Fix: removed that line. `database.py` only holds `engine`, `sessionLocal`, `Base`, and `get_db`.

---

**`ModuleNotFoundError` for `app.dependencies`**

Cause: `users.py` imported `get_db` from `app.dependencies` but that file didn't exist.

Fix: created `dependencies.py` with `from app.database import get_db`.

---

**`no such table: users` (SQLite)**

Cause: models weren't imported in the `db_session` fixture, or `:memory:` was causing separate connections with no shared state.

Fix: imported all models at the top of `conftest.py` and switched to file-based `test.db`. Models must be imported before `create_all` runs.

---

**bcrypt "password cannot be longer than 72 bytes"**

Cause: `bcrypt 5.0.0` is incompatible with `passlib`.

Fix: `pip install bcrypt==4.0.1`.

---

**`owner_id` not in response**

Fix: removed that assertion from the tests.

---

**`GET /tasks/` returns a paginated dict, not a list**

Fix: used `data["results"]` in the test instead of iterating `data` directly.

---

**`DELETE` returns `200`, test expected `204`**

Fix: updated the assertion to check for `200`.

---

## How to Run Tests

```bash
# Activate venv
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run only auth tests
python -m pytest tests/test_auth.py -v

# Run a single test
python -m pytest tests/test_tasks.py::test_create_task_success -v
```

Add to `.gitignore`:

```
test.db
__pycache__/
.pytest_cache/
venv/
.env
```

---


## Core Mental Models

```
pytest                  = automated robot that hits your API and checks the output.
conftest.py             = home for all shared setup. Fixtures live here.
fixture                 = function that creates a resource and injects it into tests.
scope="function"        = fresh fixture for every test. Tests stay independent.
scope="session"         = one fixture shared across all tests. Faster but risky — tests can bleed into each other.
dependency_overrides    = FastAPI's mechanism to swap one dependency for another at runtime.
TestClient              = dummy HTTP client. No real server, no real network, no ports.
auth_headers            = token already packed into a header dict. Plug directly into any test call.
test.db vs :memory:     = file-based SQLite shares state across connections. In-memory does not.
models in conftest.py   = must be imported before create_all so their tables get created.
```

---

## Interview Questions

**Why don't you use the real database in tests?**

The real database accumulates data, is slow, and causes conflicts in parallel test runs. A test database (SQLite file-based) is isolated, fast, and disposable.

**What is the difference between fixture scope `"function"` and `"session"`?**

`"function"` recreates the fixture before every single test — safe for independent tests. `"session"` creates it once and all tests share it — faster but tests can end up depending on each other's state.

**Why do you use `dependency_overrides`?**

To give FastAPI a test dependency instead of the production one (`get_db`). It lets you replace the real database connection without changing any application code.

**Why must models be imported in `conftest.py` before `create_all`?**

`Base.metadata.create_all` only knows about models that have been imported. If `User` and `Task` haven't been imported yet when `create_all` runs, their tables won't be created and every test will fail with "no such table".

**Why use file-based SQLite instead of `:memory:` for tests?**

SQLite `:memory:` creates a separate database for every connection. Since SQLAlchemy uses a connection pool, different parts of the test can end up talking to different empty databases. File-based `test.db` gives all connections a single shared state.