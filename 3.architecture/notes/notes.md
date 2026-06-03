# Environment Variables & `.env` Files

## The Problem

Hardcoding sensitive values like database URLs, passwords, and secret keys directly in source code is a serious security risk. If that code is pushed to GitHub, those credentials are exposed to anyone who can see the repo. This is how real companies get breached.

> **Never commit credentials to version control.** Even a private repo can be accidentally made public.

---

## The Solution

Store sensitive config in a separate `.env` file that lives only on your machine and never gets pushed to GitHub. Your code reads from that file at runtime.

### What a `.env` File Looks Like

```env
DATABASE_URL=sqlite:///./products.db
SECRET_KEY=mysupersecretkey123
DEBUG=True
```

**Rules:** no quotes, no spaces around the equals sign. Just `KEY=value`.

---

## Reading It in Python

```bash
pip3 install python-dotenv
```

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Reads `.env` file and injects all key-value pairs into OS environment variables

DATABASE_URL = os.getenv('DATABASE_URL')  # Reads a value from OS environment variables by key name
```

---

## `.gitignore` - Keeping Secrets Off GitHub

A `.gitignore` file tells Git which files to completely ignore and never push. Create it in your project root:

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

### Why Not Just `os.getenv`?

`os.getenv` works but has one critical problem: if a required variable is missing from your `.env` file, your app won't catch it until something breaks deep at runtime. You get a cryptic error instead of a clear message.

**Pydantic settings validates ALL environment variables the moment the app starts.** If something is missing, you get a clear validation error immediately - before anything else runs.

### Setup

```bash
pip3 install pydantic-settings --break-system-packages
```

### `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str

    class Config:
        env_file = '.env'

settings = Settings()
```

### Updated `database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### How Each Piece Works

| Piece | Role |
|---|---|
| `BaseSettings` | Parent class providing logic for reading `.env` files and validating values |
| `database_url: str` | Declares this variable is required and must be a string |
| `class Config` | Tells Pydantic which file to read from |
| `settings = Settings()` | Instantiates and validates - app crashes here if anything is missing |

> **Test it:** delete `DATABASE_URL` from your `.env` and restart. Pydantic immediately throws `"Field required [type=missing]"`. That is the entire value of this approach.
---

## Production-Grade Project Structure

```
backend/
├── main.py
├── config.py
├── .env              (never pushed)
├── .env.example      (pushed — shows what variables are needed)
├── .gitignore
├── requirements.txt
└── app/
    ├── database.py
    ├── models/
    │   └── products.py
    ├── schemas/
    │   └── products.py
    ├── routers/
    │   └── products.py
    └── crud/
        └── products.py
```

| Folder / File | Responsibility |
|---|---|
| `main.py` | Entry point only. Creates the FastAPI app and registers routers. Nothing else. |
| `config.py` | Pydantic settings. All env variable definitions live here. |
| `app/database.py` | SQLAlchemy engine, session factory, and Base declaration. |
| `app/models/` | SQLAlchemy table classes. One file per database table. |
| `app/schemas/` | Pydantic models for request validation and response shaping. |
| `app/routers/` | FastAPI route functions. One file per resource. Only handles HTTP. |
| `app/crud/` | All database query logic. No HTTP here. Just functions that talk to the database. |

---

## Single Responsibility Principle (SRP)

Each piece of code should do ONE thing only.

| Layer | What It Does |
|---|---|
| `routers/products.py` | Handles HTTP. Reads the request, calls a crud function, returns the response. |
| `crud/products.py` | Handles the database. No HTTP, no FastAPI. Just query logic. |

> The router calls the crud function. That is the only coupling. If your database query needs to change, you change it once in `crud` — not in every route that uses it.

---

## Pydantic Schemas — app/schemas/products.py

Schemas define the shape of data going in and coming out of your API. Completely separate from SQLAlchemy models.

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
        from_attributes = True
```

| Schema | Purpose |
|---|---|
| `ProductCreate` | Validates incoming POST request body |
| `ProductUpdate` | All fields optional — for PUT requests |
| `ProductResponse` | Defines exactly what the API returns to the client |

> `from_attributes = True` gives Pydantic permission to use dot notation, because by default Pydantic does not use dot notation — it expects dictionary style (obj["key"]). Because of this permission, Pydantic can read the SQLAlchemy object's attributes using dot notation and create its own Pydantic object.

---

## SQLAlchemy Model — app/models/products.py

```python
from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
```

> Always inherit from `Base`, not from Pydantic's `BaseModel`. These are completely different parents for completely different purposes.

---

## The CRUD Layer — app/crud/products.py

All database logic lives here. Plain functions — no HTTP, no FastAPI decorators.

```python
from sqlalchemy.orm import Session
from app.models.products import Product
from app.schemas.products import ProductCreate, ProductUpdate

def get_all_products(db: Session):
    return db.query(Product).all()

def get_product_by_id(product_id: int, db: Session):
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(product: ProductCreate, db: Session):
    new_product = Product(name=product.name, price=product.price, in_stock=product.in_stock)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(product_id: int, product: ProductUpdate, db: Session):
    existing = get_product_by_id(product_id, db)
    if product.name is not None:
        existing.name = product.name
    if product.price is not None:
        existing.price = product.price
    if product.in_stock is not None:
        existing.in_stock = product.in_stock
    db.commit()
    db.refresh(existing)
    return existing

def delete_product(product_id: int, db: Session):
    existing = get_product_by_id(product_id, db)
    db.delete(existing)
    db.commit()
```

| Pattern | Why |
|---|---|
| `Product(name=..., price=..., in_stock=...)` | Explicitly map fields — never pass a Pydantic object directly to SQLAlchemy |
| `db.add()` | Stages the new record |
| `db.commit()` | Writes to the database permanently |
| `db.refresh()` | Reloads the object from DB — how you get the auto-generated id back |
| Check `is not None` in update | Allows partial updates — only change fields the client actually sent |

---

## The Router Layer — app/routers/products.py

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import sessionLocal
from app.schemas.products import ProductCreate, ProductUpdate, ProductResponse
from app.crud.products import get_all_products, get_product_by_id, create_product, update_product, delete_product

router = APIRouter(prefix='/products', tags=['products'])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/', response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return get_all_products(db)

@router.get('/{product_id}', response_model=ProductResponse)
def fetch_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(product_id, db)
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return product

@router.post('/', status_code=201, response_model=ProductResponse)
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    return create_product(product, db)

@router.put('/{product_id}', response_model=ProductResponse)
def edit_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    existing = get_product_by_id(product_id, db)
    if existing is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return update_product(product_id, product, db)

@router.delete('/{product_id}')
def remove_product(product_id: int, db: Session = Depends(get_db)):
    existing = get_product_by_id(product_id, db)
    if existing is None:
        raise HTTPException(status_code=404, detail='Product not found')
    delete_product(product_id, db)
    return {"message": "Product deleted"}
```

| Feature | What It Does |
|---|---|
| `prefix='/products'` | Every route automatically gets `/products` prepended |
| `tags=['products']` | Groups all routes under a products section in Swagger /docs |
| `get_db()` with yield | Opens a DB session, closes it after the request finishes |
| `Depends(get_db)` | FastAPI dependency injection — automatically passes the session |
| `response_model` | FastAPI uses this to filter and shape the response |

---

## main.py

```python
from fastapi import FastAPI
from app.models.products import Product
from app.database import Base, engine
from app.routers.products import router as products_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(products_router)
```

> `Base.metadata.create_all(bind=engine)` creates all tables that do not exist yet. Run once at startup.

---

## Alembic — Database Migrations

### The Problem Without Alembic

`create_all()` only creates tables that do not exist yet. If your app is running in production with real data and you add a new column to your model, `create_all` will not touch the existing table. You need migrations.

### What Migrations Are

Think of Alembic like Git but for your database schema. Every schema change is a versioned file with an `upgrade()` and `downgrade()` function.

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

---

## requirements.txt

```bash
# Generate from your current environment
pip3 freeze > requirements.txt

# Anyone cloning the repo installs everything with
pip3 install -r requirements.txt
```

---

## Summary

| File | Type | What It Does |
|---|---|---|
| `config.py` | Config | Pydantic settings — validates all env variables at startup |
| `app/database.py` | Database | SQLAlchemy engine, session, and Base |
| `app/models/products.py` | Model | Product table definition (SQLAlchemy) |
| `app/schemas/products.py` | Schema | ProductCreate, ProductUpdate, ProductResponse (Pydantic) |
| `app/crud/products.py` | CRUD | All database query logic — get, create, update, delete |
| `app/routers/products.py` | Router | All HTTP route handlers using APIRouter |
| `main.py` | Entry Point | Creates app, registers router. Nothing else. |
| `.env` | Config | Sensitive config — never pushed to GitHub |
| `.gitignore` | Config | Prevents `.env`, `__pycache__`, `*.db` from being pushed |
| `requirements.txt` | Config | Lists all project dependencies |

---

## What Was Built

- `config.py` with Pydantic settings validating `DATABASE_URL` at startup
- `.env` file storing database URL locally
- `.gitignore` preventing secrets and cache files from reaching GitHub
- Full production-grade folder structure with `models/`, `schemas/`, `routers/`, and `crud/`
- Pydantic schemas for `ProductCreate`, `ProductUpdate`, and `ProductResponse`
- Complete CRUD layer with `get_all`, `get_by_id`, `create`, `update`, and `delete` functions
- Router layer using `APIRouter` with `/products` prefix and Swagger tags
- Dependency injection with `get_db()` using `Depends`
- Clean `main.py` that only creates the app and registers the router
- `requirements.txt` generated from the current environment
- Alembic initialized and migration commands understood
