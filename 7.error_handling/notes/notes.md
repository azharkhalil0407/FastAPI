# Relationships, Query Patterns & Error Handling

---

## Part 1: Foreign Keys

Without a foreign key, `user_id = Column(Integer)` accepts any value — 999, -1, anything. If a user gets deleted, their `user_id` stays in the products table pointing to nothing. This is called a **dangling reference** — silent data corruption with no warning from the database.

With a foreign key, PostgreSQL enforces two rules:

- **On insert:** checks the referenced user exists. Rejects invalid values.
- **On delete:** blocks deletion by default unless you specify `ondelete`.

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

Always use the table name `"users.id"`, not the class name `"User.id"`. The database knows tables, not Python classes.

---

## Part 2: `ondelete` Options

| Option | Behavior |
|--------|----------|
| `RESTRICT` (default) | Blocks user deletion if they have products. User must delete all products first. Rarely useful in real apps. |
| `CASCADE` | User deleted → products deleted automatically. Most common. Use this by default. |
| `SET NULL` | User deleted → product stays, `user_id` becomes null. Use when you want to keep the record but drop the association. |

```python
# CASCADE
user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

# SET NULL — nullable=True is required here
user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
```

**Verify the constraint exists in PostgreSQL:**

```bash
psql -d fastapi_db -c "\d products"
```

Look for:
```
Foreign-key constraints:
    "products_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
```

---

## Part 3: `relationship()`

The foreign key handles database integrity. But your Python code still doesn't know how to navigate from a user to their products without writing a manual query every time.

```python
# Without relationship() — manual every time
products = db.query(Product).filter(Product.user_id == user.id).all()

# With relationship()
products = user.products  # SQLAlchemy handles the query internally
```

Add it to the `User` model:

```python
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    products = relationship("Product")
```

`relationship()` does not touch the database schema at all. It is purely a Python/ORM convenience. The foreign key is what enforces integrity at the database level — `relationship()` just makes your code easier to write.

---

## Part 4: `back_populates`

Without `back_populates`, SQLAlchemy treats `user.products` and `product.owner` as two independent relationships. Setting `product.owner = some_user` updates the column in the database but `some_user.products` in memory stays stale. You'd need to call `db.refresh()` manually.

`back_populates` tells SQLAlchemy these are two sides of the same relationship. Change one side, the other syncs automatically in the same session.

```python
# In User model
products = relationship("Product", back_populates="owner")

# In Product model
owner = relationship("User", back_populates="products")
```

Both of these now work and stay in sync:

```python
macbook.owner = chiranjibi
# SQLAlchemy: updates macbook.user_id, removes from old user's list, adds to chiranjibi's list

chiranjibi.products.append(macbook)
# SQLAlchemy: sets macbook.user_id = chiranjibi.id
```

The string in `back_populates` must exactly match the attribute name on the other model.

---

## Part 5: `create_all` Limitation

`create_all` only creates tables that don't exist yet. It never modifies existing tables. Add a column to your model and restart the server — nothing changes in the database.

**Development workaround:**

```bash
psql -d fastapi_db -c "DROP TABLE IF EXISTS products, users CASCADE;"
# Restart server — create_all will rebuild fresh
```

`CASCADE` here drops any foreign key constraints pointing to these tables before dropping them. In production, use **Alembic migrations** instead.

---

## Part 6: User-Scoped Queries

A `GET /products/` endpoint returning all products in the database is wrong in production. A logged-in user should only see their own products.

**Router:**

```python
@router.get("/", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_all_products(db, current_user.id)
```

**CRUD:**

```python
def get_all_products(db: Session, user_id: int):
    return db.query(Product).filter(Product.user_id == user_id).all()
```

---

## Part 7: The N+1 Problem

You fetch 10 products in one query. Then for each product, you run a separate query to get the owner's details. That is 1 + 10 = 11 queries for 10 products. 100 products = 101 queries. Each query is a network round trip between your app and the database. Performance degrades fast.

---

## Part 8: `joinedload()` — Eager Loading

Fix N+1 by fetching products and their owners in a single JOIN query instead of looping.

The SQL SQLAlchemy generates:

```sql
SELECT products.*, users.*
FROM products
JOIN users ON products.user_id = users.id
WHERE products.user_id = ?
```

One query. Everything comes back together.

```python
from sqlalchemy.orm import joinedload

def get_all_products(db: Session, user_id: int):
    return (
        db.query(Product)
        .options(joinedload(Product.owner))
        .filter(Product.user_id == user_id)
        .all()
    )
```

`.options(joinedload(Product.owner))` tells SQLAlchemy to JOIN the users table in the same query. `Product.owner` refers to the `owner` relationship defined on the `Product` model.

Update the response schema to include the owner:

```python
from app.schemas.users import UserResponse

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool
    user_id: int
    owner: UserResponse

    class Config:
        from_attributes = True
```

**`joinedload` vs `selectinload`:**

| | `joinedload` | `selectinload` |
|---|---|---|
| How | Single query with a JOIN | Second query using `WHERE id IN (...)` |
| Best for | Simple, standard relationships | Complex or deeply nested relationships |
| Risk | Can produce duplicate data in one-to-many | No N+1, cleaner for complex cases |

For most standard cases, `joinedload` is fine.

---

## Part 9: Circular Import Fix

`User` model references `"Product"`. `Product` model references `"User"`. Neither file can finish loading without the other. Python hits a circular reference.

```python
from __future__ import annotations

# rest of your imports below
```

This tells Python to treat type annotations as strings and not evaluate them at import time. By the time SQLAlchemy resolves these strings, all files are loaded and the classes exist. Must be the **absolute first line** in both `users.py` and `products.py` — before any imports, before any comments. Missing it in one file still causes an error.

---

## Part 10: `IntegrityError` — Why 500 Was Happening and How to Fix It

When you call `POST /products/` with `user_id=999` and that user doesn't exist, here is what happens step by step:

1. `db.add(new_product)` — only registers the object in the SQLAlchemy session. Nothing goes to the database yet.
2. `db.commit()` — this is where the actual SQL insert goes to PostgreSQL.
3. PostgreSQL rejects it — foreign key violation.
4. `psycopg2` catches the database error.
5. SQLAlchemy wraps it into `sqlalchemy.exc.IntegrityError`.
6. Since there is no `try/except`, the exception bubbles up to FastAPI's default handler.
7. FastAPI returns `500 Internal Server Error`.

The fix is a `try/except` around `db.commit()` in the CRUD layer, and catching it in the router to return a proper HTTP response.

**CRUD layer:**

```python
from sqlalchemy.exc import IntegrityError

def create_product(product: ProductCreate, db: Session, user_id: int):
    new_product = Product(
        name=product.name,
        price=product.price,
        in_stock=product.in_stock,
        user_id=user_id
    )
    db.add(new_product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(new_product)
    return new_product
```

`db.rollback()` is required because when `db.commit()` fails, the SQLAlchemy session enters a broken state. No further database operations will work in that session until you roll back. `raise` (bare) re-raises the same exception so the router can catch it.

**Router layer:**

```python
from sqlalchemy.exc import IntegrityError

@router.post("/", status_code=201, response_model=ProductResponse)
def add_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return create_product(product, db, current_user.id)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="User does not exist")
```

**Architectural rule:** the CRUD layer catches database errors and re-raises them. The router layer converts them into HTTP responses. The CRUD layer should never know about HTTP status codes. Clean separation.

---

## Part 11: Pydantic Field Validators

Without validation, your API accepts anything — empty strings, negative prices, names with numbers. All of it goes straight to the database.

```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-zA-Z ]+$")
    price: float = Field(..., gt=0)
    in_stock: bool
```

- `...` means the field is required, not optional.
- `min_length=2, max_length=100` — name must be between 2 and 100 characters.
- `pattern=r"^[a-zA-Z ]+$"` — only letters and spaces allowed.
- `gt=0` — price must be greater than zero.

**Common validators:**

| Validator | Meaning |
|-----------|---------|
| `gt=0` | greater than 0 |
| `ge=0` | greater than or equal to 0 |
| `lt=100` | less than 100 |
| `le=100` | less than or equal to 100 |
| `min_length=2` | minimum 2 characters |
| `max_length=100` | maximum 100 characters |
| `pattern=r"..."` | must match this regex |

When validation fails, FastAPI automatically returns `422 Unprocessable Entity`. You don't need to do anything extra.

---

## Part 12: Global Exception Handlers

Without global handlers, your API returns errors in three different shapes:

- Pydantic errors: `422` with a complex nested array structure
- `HTTPException`: `400/404` with `{"detail": "message"}`
- Unhandled exceptions: `500` with generic text

The fix is registering global handlers in `main.py` that normalize everything into one consistent shape:

```json
{
  "status": "error",
  "message": "descriptive message here"
}
```

**Handler for Pydantic validation errors:**

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid input"}
    )
```

**Handler for `HTTPException`:**

```python
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )
```

`exc.status_code` and `exc.detail` come from whatever you passed when raising. Both handlers must have unique function names — if they share a name, Python silently overwrites the first with the second.

**Complete `main.py`:**

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid input"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )
```

---

## Part 13: Security Fix — Never Take `user_id` from the Client

If `user_id` is a field in `ProductCreate`, any client can send `user_id: 5` and create a product under someone else's account. That is a direct security vulnerability.

**Fix: remove `user_id` from the request schema and pull it from the JWT token instead.**

**Step 1 — remove from schema:**

```python
class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool
    # user_id removed
```

**Step 2 — router pulls it from the token:**

```python
@router.post("/", status_code=201, response_model=ProductResponse)
def add_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return create_product(product, db, current_user.id)
```

**Step 3 — CRUD accepts it as a parameter:**

```python
def create_product(product: ProductCreate, db: Session, user_id: int):
    new_product = Product(
        name=product.name,
        price=product.price,
        in_stock=product.in_stock,
        user_id=user_id  # comes from token, not client
    )
```

The client can no longer supply `user_id` at all. Whatever user is authenticated via JWT is who the product gets assigned to.

---

## Part 14: `HTTPException` vs Custom Exceptions

`HTTPException` is FastAPI's built-in. You raise it directly with a status code and message.

```python
raise HTTPException(status_code=404, detail="Product not found")
```

Custom exceptions are your own classes with a registered handler:

```python
class ProductNotFoundException(Exception):
    pass

@app.exception_handler(ProductNotFoundException)
async def product_not_found_handler(request: Request, exc: ProductNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": "Product not found"}
    )

# Then anywhere in your code:
raise ProductNotFoundException()
```

**Why custom exceptions matter:** the CRUD layer shouldn't know about HTTP status codes. When you raise `ProductNotFoundException()` from CRUD, the router or handler decides the status code. Also, if the same exception can be raised from 10 places, you write the response logic once in the handler instead of repeating it everywhere.

For a project at your current scale, `HTTPException` is fine. But understand the pattern for interviews and larger codebases.

---

## Core Mental Models

```
ForeignKey           = database police. Enforces referential integrity.
ondelete             = what happens when the parent is deleted (CASCADE / SET NULL / RESTRICT).
relationship()       = Python shortcut only. Zero impact on schema.
back_populates       = both sides sync automatically in memory. No db.refresh() needed.
create_all           = creates new tables only. Never modifies existing ones.
N+1 problem          = 1 query for list + N queries for each related object. Avoid it.
joinedload()         = fetch related objects in the same query via JOIN.
from __future__      = circular import fix. First line. Both files.
IntegrityError       = database constraint violated (foreign key, unique, etc.)
db.rollback()        = required after failed commit. Cleans the session state.
raise (bare)         = re-raises the same exception to the layer above.
Field(gt=0)          = Pydantic validates before data reaches your code.
422                  = validation failed. FastAPI sends this automatically.
Global handler       = normalize all errors into one consistent shape.
user_id from token   = never trust the client for ownership. Always use JWT.
Custom exception     = keeps CRUD layer ignorant of HTTP. Handler decides status code.
```

---

## Interview Questions

**What is a foreign key?**
A database-level constraint that enforces referential integrity. It ensures a child table's column always references an existing primary key in the parent table, and defines what happens on deletion.

**What is the difference between `ForeignKey` and `relationship()`?**
`ForeignKey` lives in the database schema and enforces integrity. `relationship()` is purely an ORM convenience in Python that lets you navigate related objects without writing manual filter queries.

**Why use `back_populates`?**
Without it, SQLAlchemy treats both sides as independent. With it, changing one side automatically updates the other in memory within the same session — no manual refresh needed.

**What is the N+1 problem?**
Fetching a list of records in one query, then running a separate query for each record's related data. Total queries = N+1. Each query is a network round trip, so performance degrades as N grows.

**How do you fix N+1?**
Use `joinedload()`. It fetches the main records and their related data in a single JOIN query.

**Why doesn't `create_all` modify existing tables?**
It only creates tables that don't exist yet. For schema changes on existing tables, use Alembic migrations.

**How do you handle `IntegrityError`?**
Wrap `db.commit()` in `try/except` in the CRUD layer. Catch `IntegrityError`, call `db.rollback()` to clean the session, then re-raise. The router catches it and raises `HTTPException` with the appropriate status code.

**Why is `db.rollback()` necessary?**
When a commit fails, the SQLAlchemy session enters a broken state. No further operations will work until you roll back. It resets the session to a clean state.

**Why use Pydantic `Field` validators?**
To validate client input before it reaches your database layer. Price must be positive, name must meet length and format requirements. Pydantic rejects invalid data automatically with a 422 response.

**Why do you need global exception handlers?**
To return a consistent error shape across all error types. Without them, Pydantic errors, HTTP exceptions, and unhandled exceptions all have different response formats. Clients need predictable structure.

**Why shouldn't `user_id` come from the client?**
A malicious user can send any `user_id` and create records under someone else's account. Pull it from the JWT token instead — it's cryptographically signed and can't be forged.

**What is the difference between `HTTPException` and a custom exception?**
`HTTPException` is FastAPI built-in and ties the status code directly to where you raise it. Custom exceptions separate that concern — CRUD raises a domain exception, the handler decides the HTTP response. Cleaner architecture, better reusability.