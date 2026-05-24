# Day 2 - SQLAlchemy + Database Integration

## How the Architecture Changed

- **Day 1**: Client → FastAPI → Dictionary (in memory, resets on restart)
- **Day 2**: Client → FastAPI → SQLAlchemy → SQLite Database (on disk, persists forever)

The dictionary was temporary. The database is permanent. Restart your server a hundred times, the data stays.

---

## SQLite vs PostgreSQL vs SQLAlchemy

- **SQLite**: A simple file-based database that lives on your disk. Zero setup. Great for learning and small projects. Your data is stored in a `.db` file in your project folder.
- **PostgreSQL**: A full production-grade database server. What real companies run in production. More powerful, handles concurrent users, scales well.
- **SQLAlchemy**: Not a database. A Python library that sits between your FastAPI code and whichever database you're using. You write Python, it translates to SQL. Works with both SQLite and PostgreSQL.

The flow: FastAPI talks to SQLAlchemy. SQLAlchemy talks to the database. You swap the connection string to switch databases. Everything else stays the same.

---

## Project Structure (Three Files)

| File | Purpose |
|---|---|
| `database.py` | Sets up the database connection, session factory, and Base class. |
| `models.py` | Defines your database tables as Python classes. |
| `main.py` | Your FastAPI routes. Same as before but now talking to the database. |

---

## database.py - Explained

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./products.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- **`engine`**: The actual connection pipeline to your database. You give it a URL that tells it what database to use and where it lives. Always there, always open.
- **`SessionLocal`**: A factory for sessions. Every time you call `SessionLocal()` you get a fresh session. Think of it as opening a new conversation with the database.
- **`Base`**: A parent class that all your SQLAlchemy models inherit from. It internally tracks every table class you define so `create_all` knows what to build.

---

## Session Mental Model

Everything you do inside a session (adding, updating, deleting) is staged locally in memory first. Nothing touches the actual database until you call `commit()`. Then the session sends it all through the engine in one go.

| Concept | What it does |
|---|---|
| `engine` | The pipeline. Always there. Knows where the database is. |
| `session` | One open conversation through that pipeline. Opened per request, closed after. |
| `commit()` | The moment everything staged locally gets pushed to the database permanently. |
| `rollback()` | Cancels everything staged. Nothing got saved so nothing is corrupted. |

---

## models.py - Database Table as a Python Class

```python
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)
    in_stock = Column(Boolean, default=True)
```

Why `Column(String)` and not `str`? SQLAlchemy operates at the database level, not the Python level. It needs to know what database column type to create. `String` translates to `VARCHAR`, `Integer` to `INTEGER`, `Boolean` to `BOOLEAN`. Python's `str`/`int`/`bool` are Python concepts — SQLAlchemy doesn't speak those.

| Syntax | What it means |
|---|---|
| `class Product(Base)` | Inherits from Base so SQLAlchemy knows this is a table definition. |
| `__tablename__` | The actual name of the table in the database. |
| `primary_key=True` | Every row gets a unique auto-generated id automatically. |
| `index=True` | Makes lookups by id faster. |
| `default=True` | If `in_stock` is not provided, it defaults to `True`. |

---

## Pydantic Model vs SQLAlchemy Model

| Pydantic Model | SQLAlchemy Model |
|---|---|
| Validates incoming API request data | Represents a table in the database |
| Defines what the request body looks like | Defines how data is stored on disk |
| Uses `name: str` syntax | Uses `name = Column(String)` syntax |
| Inherits from `BaseModel` (Pydantic) | Inherits from `Base` (SQLAlchemy) |

---

## Dependency Injection + get_db()

Every request needs a fresh database session. FastAPI's `Depends` system handles this automatically. You write `get_db()` once and inject it into every route that needs a database.

```python
def get_db():
    db = SessionLocal()  # open a fresh session
    try:
        yield db          # hand it to the route function, pause here
    finally:
        db.close()        # always runs after the request is done
```

- **Why `yield` and not `return`?** `return` ends the function immediately — `db.close()` would never run. `yield` pauses the function, lets the route do its work, then resumes and closes the session. The `finally` block guarantees cleanup even if the route crashes.
- **Dependency Injection**: Instead of each route creating its own session manually, FastAPI injects it from outside via `Depends(get_db)`. Loose coupling, clean code, easy to swap later.

---

## create_all - Creating Tables on Startup

```python
models.Base.metadata.create_all(bind=engine)
```

This line runs once when your server starts. `Base` tracks all your SQLAlchemy models. `metadata` holds their structure (table names, column names, column types). `create_all` goes through that list and creates the actual tables in the database if they don't already exist. `bind=engine` tells it which database to create them in.

> **Important**: `import models` must happen before `create_all` runs. The import loads the file and registers all table classes onto `Base`. Without it, `Base` would have no idea about your `Product` table.

---

## SQLAlchemy Queries - No Raw SQL Needed

| Query | What it does |
|---|---|
| `db.query(Product).all()` | `SELECT * FROM products` — fetch every row. |
| `db.query(Product).filter(Product.id == product_id).first()` | `SELECT * FROM products WHERE id = ? LIMIT 1` — fetch one row by id. |
| `db.add(new_product)` | Stage a new row for insertion. Not saved yet. |
| `db.commit()` | Push everything staged to the database permanently. |
| `db.refresh(obj)` | Reload the object from DB to get auto-generated fields like `id`. |
| `db.delete(obj)` | Stage a row for deletion. Not deleted until `commit`. |

---

## Converting Pydantic to SQLAlchemy

```python
new_product = Product(**product.dict())

# product.dict() gives you:
# {"name": "macbook", "price": 100000, "in_stock": True}

# ** unpacks it, so it becomes:
# Product(name="macbook", price=100000, in_stock=True)

# This creates a SQLAlchemy object representing one new row
# ready to be inserted into the database.
```

---

## Endpoint Behavior (Products API)

```python
# Session is injected per request via Depends(get_db)
db: Session = Depends(get_db)
```

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/products` | Returns all rows from the products table. |
| `GET` | `/products/{product_id}` | Fetches one product by id. Raises `404` if not found. |
| `POST` | `/products` | Creates a new product (status 201). Auto-generates the id. |
| `PUT` | `/products/{product_id}` | Partial update. Raises `404` if not found. Only updates non-`None` fields. |
| `DELETE` | `/products/{product_id}` | Deletes the product. Raises `404` if not found. Returns confirmation message. |

---

## Full main.py - Final Code

```python
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import models
from database import engine, SessionLocal
from models import Product

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class ProductSchema(BaseModel):
    name: str
    price: float
    in_stock: bool

class UpdateProductSchema(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/products')
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get('/products/{product_id}')
def fetch_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail='product not found')
    return product

@app.post('/products', status_code=201)
def create_product(product: ProductSchema, db: Session = Depends(get_db)):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.put('/products/{product_id}')
def update_product(product_id: int, product: UpdateProductSchema, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.id == product_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail='product not found')
    if product.name is not None:
        existing.name = product.name
    if product.price is not None:
        existing.price = product.price
    if product.in_stock is not None:
        existing.in_stock = product.in_stock
    db.commit()
    db.refresh(existing)
    return existing

@app.delete('/products/{product_id}')
def delete_product(product_id: int, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.id == product_id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail='product not found')
    db.delete(existing)
    db.commit()
    return {'message': 'product deleted'}
```

---

## What Was Built on Day 2

- Set up a SQLite database connection using SQLAlchemy
- Defined a `Product` table as a Python class in `models.py`
- Created `database.py` with `engine`, `SessionLocal`, and `Base`
- Used `create_all` to auto-create tables on server startup
- Implemented dependency injection with `get_db()` and `Depends`
- Built full CRUD API backed by a real persistent database
- Verified data persists across server restarts