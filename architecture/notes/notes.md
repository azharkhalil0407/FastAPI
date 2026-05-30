# Environment Variables, Project Structure, CRUD Layer, and Alembic

---

## Environment Variables and .env Files

### The Problem

Hardcoding sensitive values like database URLs, passwords, and secret keys directly in source code is a serious security risk. If that code is pushed to GitHub, those credentials are exposed to anyone who can see the repo. This is how real companies get breached.

> Never commit credentials to version control. Even a private repo can be accidentally made public.

### The Solution

Store sensitive config in a separate `.env` file that lives only on your machine and never gets pushed to GitHub. Your code reads from that file at runtime.

### What a .env File Looks Like

```env
DATABASE_URL=sqlite:///./products.db
SECRET_KEY=mysupersecretkey123
DEBUG=True
```

Rules: no quotes, no spaces around the equals sign. Just `key=value`.

### Reading It in Python

```bash
pip3 install python-dotenv
```

```python
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env and loads into environment
DATABASE_URL = os.getenv('DATABASE_URL')  # fetches value by key
```

| Function | What It Does |
|---|---|
| `load_dotenv()` | Reads `.env` file and injects all key-value pairs into OS environment variables |
| `os.getenv('KEY')` | Reads a value from OS environment variables by key name |

---

## .gitignore - Keeping Secrets Off GitHub

A `.gitignore` file tells Git which files to completely ignore and never push. Create it in your project root.

```
.env
__pycache__/
*.pyc
*.db
```

| Entry | Why You Ignore It |
|---|---|
| `.env` | Contains secrets - never push credentials |
| `__pycache__/` | Python compiled cache, no reason to push |
| `*.pyc` | Compiled bytecode files |
| `*.db` | Database files like `products.db` |

---

## Pydantic Settings Management

### Why Not Just os.getenv?

`os.getenv` works but has one critical problem: if a required variable is missing from your `.env` file, your app will not catch it until something breaks deep at runtime. You get a cryptic error instead of a clear message.

Pydantic settings validates ALL environment variables the moment the app starts. If something is missing, you get a clear validation error immediately before anything else runs.

### Setup

```bash
pip3 install pydantic-settings --break-system-packages
```

### config.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str

    class Config:
        env_file = '.env'

settings = Settings()
```

### Updated database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

| Piece | Role |
|---|---|
| `BaseSettings` | Parent class providing logic for reading `.env` files and validating values |
| `database_url: str` | Declares this variable is required and must be a string |
| `class Config` | Tells Pydantic which file to read from |
| `settings = Settings()` | Instantiates and validates - app crashes here if anything is missing |

> Test it: delete `DATABASE_URL` from your `.env` and restart. Pydantic immediately throws `"Field required [type=missing]"`. That is the entire value of this approach.

---

## Production-Grade Project Folder Structure

In a real backend project, every file has a single responsibility. You do not dump everything in one folder. The structure below is the standard pattern used across the Python backend industry.

```
fastapi-backend/
├── main.py
├── config.py
├── .env              (never pushed)
├── .gitignore
├── requirements.txt
└── app/
    ├── __init__.py
    ├── database.py
    ├── models/
    │   ├── __init__.py
    │   └── product.py
    ├── schemas/
    │   ├── __init__.py
    │   └── product.py
    ├── routers/
    │   ├── __init__.py
    │   └── product.py
    └── crud/
        ├── __init__.py
        └── product.py
```

| Folder / File | Responsibility |
|---|---|
| `main.py` | Entry point only. Creates the FastAPI app and registers routers. Nothing else. |
| `config.py` | Pydantic settings. All env variable definitions live here. |
| `app/database.py` | SQLAlchemy engine, session factory, and Base declaration. |
| `app/models/` | SQLAlchemy table classes. One file per database table. |
| `app/schemas/` | Pydantic models for request validation and response shaping. Separate from ORM models. |
| `app/routers/` | FastAPI route functions. One file per resource. Only handles HTTP. |
| `app/crud/` | All database query logic. No HTTP here. Just functions that talk to the database. |
| `__init__.py` | Empty file that tells Python this folder is a module. |

---

## Single Responsibility Principle (SRP)

Each piece of code should do ONE thing only.

Before the restructure, route functions were doing two things: handling HTTP and querying the database. Fine for learning, but terrible at scale.

| Layer | What It Does |
|---|---|
| `routers/product.py` | Handles HTTP. Reads the request, calls a crud function, returns the response. |
| `crud/product.py` | Handles the database. No HTTP, no FastAPI. Just query logic. |

> The router calls the crud function. That is the only coupling. If your database query needs to change, you change it once in `crud` - not in every route that uses it.

---

## Pydantic Schemas (Request + Response Shapes)

Schemas define the shape of data going in and coming out of your API. They live in `app/schemas/` and are completely separate from your SQLAlchemy models.

```python
from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    price: float
    in_stock: bool

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool

    class Config:
        from_attributes = True  # lets Pydantic read SQLAlchemy objects
```

| Schema | Purpose |
|---|---|
| `ProductCreate` | Validates incoming POST request body |
| `ProductUpdate` | All fields optional - for PATCH/PUT requests |
| `ProductResponse` | Defines exactly what the API returns to the client |

> `from_attributes = True` tells Pydantic it can read data directly from SQLAlchemy ORM objects instead of requiring plain dicts.

---

## The CRUD Layer

All database logic lives in `app/crud/product.py`. These are plain functions - no HTTP, no FastAPI decorators. Just database operations.

```python
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

def get_all_products(db: Session):
    return db.query(Product).all()

def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, product: ProductCreate):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(db: Session, product_id: int, product: ProductUpdate):
    existing = get_product_by_id(db, product_id)
    if product.name is not None: existing.name = product.name
    if product.price is not None: existing.price = product.price
    if product.in_stock is not None: existing.in_stock = product.in_stock
    db.commit()
    db.refresh(existing)
    return existing

def delete_product(db: Session, product_id: int):
    existing = get_product_by_id(db, product_id)
    db.delete(existing)
    db.commit()
```

> Key pattern: `update_product` and `delete_product` both call `get_product_by_id` instead of rewriting the query. One place to change if the logic ever needs updating.

---

## The Router Layer and APIRouter

Routes live in `app/routers/product.py`. This file only handles HTTP. It calls crud functions for all database work.

Instead of using `app.get()` directly, you use `router.get()`. A router is a mini FastAPI app that handles a group of related routes. You register it in `main.py`.

| Feature | What It Does |
|---|---|
| `prefix='/products'` | Every route in this file automatically gets `/products` prepended. No need to repeat it. |
| `tags=['products']` | Groups all these routes under a `products` section in Swagger `/docs` |
| `app.include_router(router)` | Registers the router with the main FastAPI app in `main.py` |

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.crud import product as crud

router = APIRouter(prefix='/products', tags=['products'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/')
def list_products(db: Session = Depends(get_db)):
    return crud.get_all_products(db)

@router.get('/{product_id}')
def fetch_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='product not found')
    return product
```

### Clean main.py

After the restructure, `main.py` is minimal. Its only job is to create the app and register routers.

```python
from fastapi import FastAPI
from app.routers.product import router as products_router
from app.models import product as models
from app.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(products_router)
```

---

## Alembic - Database Migrations (Introduction)

Alembic is a migration tool for SQLAlchemy. It tracks every change you make to your database schema over time as versioned files.

### The Problem Without Alembic

`create_all()` only creates tables that do not exist yet. If your app is running in production with real data and you add a new column to your model, `create_all` will not touch the existing table. Your new column simply does not appear. You need migrations.

### What Migrations Are

Think of Alembic like Git but for your database schema. Every schema change is a versioned file with an `upgrade()` and `downgrade()` function. You can apply changes forward or roll them back.

| File / Folder | Purpose |
|---|---|
| `env.py` | Connects Alembic to your SQLAlchemy models and database. Most important file. |
| `script.py.mako` | Template used to generate new migration files. |
| `versions/` | Where all your migration files live. Empty until you generate your first migration. |

```bash
# Initialize Alembic
python3 -m alembic init migrations

# Generate a migration after a model change
alembic revision --autogenerate -m 'add category column'

# Apply the migration
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

> Full Alembic wiring is covered in Week 2 when you start building table relationships.

---

## requirements.txt

This file lists all packages your project depends on. Anyone who clones your repo can install everything with one command.

```bash
# Generate from your current environment
pip3 freeze > requirements.txt

# Anyone cloning the repo installs everything with
pip3 install -r requirements.txt
```

---

## Summary - What You Built on Day 3

| File | Type | What It Does |
|---|---|---|
| `config.py` | Config | Pydantic settings - validates all env variables at startup |
| `app/database.py` | Database | SQLAlchemy engine, session, and Base |
| `app/models/product.py` | Model | Product table definition (SQLAlchemy) |
| `app/schemas/product.py` | Schema | `ProductCreate`, `ProductUpdate`, `ProductResponse` (Pydantic) |
| `app/crud/product.py` | CRUD | All database query logic - get, create, update, delete |
| `app/routers/product.py` | Router | All HTTP route handlers using `APIRouter` |
| `main.py` | Entry Point | Creates app, registers router. Nothing else. |
| `.env` | Config | Sensitive config - never pushed to GitHub |
| `.gitignore` | Config | Prevents `.env`, `__pycache__`, `*.db` from being pushed |
| `requirements.txt` | Config | Lists all project dependencies |

---

## Key Concepts from Day 3

- Environment variables keep secrets out of source code
- Pydantic settings validate config at startup, not at runtime failure
- `.gitignore` prevents `.env` and database files from reaching GitHub
- Single Responsibility Principle - each file does one thing only
- Routers handle HTTP. CRUD handles the database. Never mix them.
- `APIRouter` groups related routes and auto-prefixes all paths
- `ProductResponse` schema controls exactly what gets sent to the client
- Alembic is how you manage schema changes safely in production