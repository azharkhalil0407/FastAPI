# SQLite to PostgreSQL Migration

## Why PostgreSQL over SQLite?

SQLite only allows one write at a time. FastAPI is multi-threaded, so concurrent writes can corrupt the file. SQLite also lacks features like schemas, user roles, row-level security, and full-text search. In production, PostgreSQL or MySQL is the standard — SQLite is only for embedded systems or mobile apps.

---

## Installation and Startup

```bash
brew install postgresql@15
brew services start postgresql@15  # runs as background service on every reboot
brew services list | grep postgresql  # verify it's running
```

---

## psql Basics

`psql` is PostgreSQL's command-line tool. Enter the shell with `psql postgres` — `postgres` is the default database PostgreSQL creates automatically.

```bash
psql postgres          # enter the shell
psql -l                # list all databases
psql -d fastapi_db -c "\dt"  # list all tables in fastapi_db without entering shell
```

---

## Creating a Database

```bash
createdb fastapi_db    # from terminal directly

# or inside psql shell:
CREATE DATABASE fastapi_db;
```

---

## Python Connector

```bash
pip install psycopg2-binary
```

`psycopg2` is Python's PostgreSQL adapter — SQLAlchemy uses it internally. The `-binary` version comes pre-compiled, so no system dependencies needed. Fine for development.

---

## Database URL Change

```python
# Before (SQLite)
DATABASE_URL = "sqlite:///./fastapi.db"

# After (PostgreSQL)
DATABASE_URL = "postgresql://mac@localhost/fastapi_db"
# With password:
DATABASE_URL = "postgresql://username:password@localhost:5432/fastapi_db"
```

**URL breakdown:**
- `postgresql://` — driver
- `mac` — DB username
- `@localhost` — server
- `fastapi_db` — database name
- `5432` — PostgreSQL's default port

---

## Engine Change

```python
# SQLite required this:
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# PostgreSQL — just this:
engine = create_engine(DATABASE_URL)
```

SQLite is file-based and restricts connections to the thread that created them. `check_same_thread=False` was a workaround for FastAPI's multi-threading. PostgreSQL is a server — it handles multiple threads natively, so this option doesn't exist in its driver.

---

## Forcing Table Creation

If a table is missing after server restart, import all models explicitly:

```bash
python3 -c "from app.database import Base, engine; from app.models.products import Product; from app.models.users import User; Base.metadata.create_all(bind=engine)"
```

`create_all` only creates tables that don't exist yet. If models aren't imported at startup, tables won't be created automatically.

---

## Core Mental Model

- **SQLite** = a file on disk. Thread safety is your problem.
- **PostgreSQL** = a running server. It handles concurrency for you.

---

# Foreign Keys and Relationships

## Why Foreign Keys?

Without a foreign key, `user_id = Column(Integer)` accepts any value — 999, -1, 0. If a user is deleted, the product still holds their `user_id`. This is called a **dangling reference** — silent data corruption.

With a foreign key, PostgreSQL enforces on insert that the referenced user exists, and on delete it follows whatever behavior you specify.

---

## `ondelete` Options

| Option | Behavior |
|--------|----------|
| `RESTRICT` (default) | Blocks user deletion if they have products. You must delete products first. |
| `CASCADE` | User deleted → products deleted automatically. Most common, best user experience. |
| `SET NULL` | User deleted → product stays, but `user_id` becomes null. Useful when you want to keep the record but drop the association. |

---

## Correct Foreign Key Syntax

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="products")
```

**Two common mistakes:**
- Using the class name `"User.id"` instead of the table name `"users.id"`
- Forgetting to import `ForeignKey`

---

## `relationship()` — Python Navigation Shortcut

```python
# Without relationship() — manual query required
products = db.query(Product).filter(Product.user_id == user.id).all()

# With relationship()
products = user.products  # SQLAlchemy handles the query internally
```

`relationship()` does not affect the database schema at all. It is purely a Python convenience that tells SQLAlchemy how to navigate between related objects.

---

## `back_populates` — Two-Way Sync

```python
# In User model
products = relationship("Product", back_populates="owner")

# In Product model
owner = relationship("User", back_populates="products")
```

Without `back_populates`, setting `product.owner = user` updates the column but `user.products` stays stale in memory. With it, SQLAlchemy keeps both sides synced — in the database and in Python objects — automatically.

---

## `create_all` Limitation

`create_all` only creates tables that don't exist. It never modifies existing tables. If you add a column to a model and restart the server, nothing changes in the database.

**Development workaround:**

```bash
psql -d fastapi_db -c "DROP TABLE IF EXISTS products, users CASCADE;"
# Then restart the server — create_all will rebuild fresh
```

`CASCADE` here drops any constraints pointing to these tables before dropping them. In production, use **Alembic migrations** instead.

---

## Circular Import Fix

When `User` references `Product` and `Product` references `User`, neither file can load without the other being defined first.

```python
from __future__ import annotations

# rest of your imports below
```

This tells Python to treat type hints as strings and not evaluate them at import time. Must be the **very first line** in both `users.py` and `products.py`. Missing it in one file will still cause an error.

---

## Verifying the Constraint

```bash
psql -d fastapi_db -c "\d products"
```

Look for this in the output:

```
Foreign-key constraints:
    "products_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
```

This confirms the constraint exists at the database level, not just in SQLAlchemy.