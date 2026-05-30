# APIs and FastAPI Basics

## What is an API and FastAPI?

- **API**: A messenger between a client and a server. The client requests data, the API fetches it, and sends back a response.
- **FastAPI**: A Python library for building the server side. Lighter and faster than Flask or Django for pure API work. Auto-generates Swagger docs at `/docs` with zero extra code.

---

## Server Setup (Uvicorn + app object)

```python
from fastapi import FastAPI

app = FastAPI()  # All routes and config attach to this object
```

Run the server:

```bash
python3 -m uvicorn main:app --reload
```

- Uvicorn is an ASGI server. It listens on port 8000 and passes HTTP requests to your app object.
- `--reload` restarts the server on every file save.
- Visit `/docs` for auto-generated Swagger UI to test endpoints visually.

---

## Routing Concepts

| Concept | Description |
|---|---|
| **Registered Route** | A URL path you define using a decorator. FastAPI keeps an internal list of all registered routes. Any unregistered path returns 404. |
| **Decorator** | `@app.get('/')` wraps the function below it and registers it as a GET request handler for that path. |
| **Path Parameter** | A variable inside curly braces in the URL, e.g. `/users/{user_id}`. The function parameter must match the exact same name. Type hints enforce the type automatically. |
| **Query Parameter** | Appears after `?` in the URL, e.g. `/search?keyword=hello`. Any function param not in curly braces is automatically treated as a query param by FastAPI. |

---

## HTTP Methods and CRUD

| Method | What it does |
|---|---|
| `GET` | Fetch data. Nothing is created or changed. |
| `POST` | Send data to create something new. Data travels in the request body. |
| `PUT` | Update an existing resource. Only provided fields are changed. |
| `DELETE` | Remove a resource by its ID. |

---

## Pydantic Data Validation

Pydantic validates incoming data. Define the expected shape as a class that inherits from `BaseModel`. FastAPI uses it automatically on every request.

```python
from pydantic import BaseModel
from typing import Optional

# Create model - all fields required
class Product(BaseModel):
    name: str
    price: float

# Update model - all fields optional
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
```

- **Create model**: All fields are required. Wrong type or missing field is rejected before your code even runs.
- **Update model**: Use `Optional[type] = None` for each field. Only updates fields that are not `None`.
- **`.dict()`**: Converts a Pydantic object to a plain Python dict for storage. After this, use square brackets `[ ]`, not dot notation.

---

## HTTP Status Codes

| Code | Meaning | When to use |
|---|---|---|
| `200` | OK | Default for successful GET responses. |
| `201` | Created | Set in decorator: `status_code=201`. Used for successful POST. |
| `400` | Bad Request | e.g. duplicate ID on create. |
| `404` | Not Found | Resource does not exist. |
| `500` | Internal Server Error | Something broke on the server side. |

### Raising errors with HTTPException

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="product not found")
```

FastAPI catches it and converts it into a proper error response automatically.

---

## Endpoint Behavior (Products API)

```python
products = {}  # Dictionary used as in-memory storage
```

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/products` | Returns the entire `products` dictionary. |
| `GET` | `/products/{product_id}` | Fetches one product. Raises `404` if not found. |
| `POST` | `/products/{product_id}` | Creates product (status 201). Raises `400` if ID already exists. Stores `product.dict()`. |
| `PUT` | `/products/{product_id}` | Partial update. Raises `404` if not found. Only updates non-`None` fields. |
| `DELETE` | `/products/{product_id}` | Removes product with `.pop()`. Raises `404` if not found. Returns confirmation message. |
| `GET` | `/` | Root route returning name and age as JSON. |
| `GET` | `/items/{item_id}` | Path parameter demo. |
| `GET` | `/search?keyword=` | Query parameter demo. |

---

## What Was Built

- Root route returning name and age as JSON
- GET with path parameter `/items/{item_id}`
- GET with query parameter `/search?keyword=`
- Pydantic model validation
- POST create with 201 and 400 handling
- GET fetch with 404 handling
- PUT partial updates with optional fields
- DELETE with confirmation response
- GET all products from dictionary storage
