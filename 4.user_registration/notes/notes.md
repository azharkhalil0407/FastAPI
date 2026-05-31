# Password Hashing + User Registration

---

## Key Concepts

- Never store plain text passwords in a database
- Hashing is a one-way transformation — you cannot reverse it
- bcrypt is intentionally slow — makes brute force attacks expensive
- Always check for duplicate emails before creating a user
- Never return the password field in any API response
- SQLAlchemy models inherit from `Base` — never from Pydantic's `BaseModel`
- Schemas control what comes in and what goes out — keep them separate

---

## Why Plaintext Passwords Are Dangerous

If you store passwords as plain text and your database gets hacked, every single user's password is immediately readable. Since most people reuse passwords across Gmail, banking, and other apps, one database breach becomes a life-ruining event for your users.

This is not a rare scenario. It happens to real companies regularly.

**The rule is simple: never store what the user typed. Store a hash of it.**

---

## What Hashing Is

Hashing is a one-way mathematical transformation. You put a password in, you get a long unreadable string out. You cannot reverse it.

```
"abc123"  →  "$2b$12$KIXoRzrQjfBpFtTmJGKnOeHvQwZzXmYkLpQdRsNgAuWvBcDeFgHiJ"
```

On login, you hash what the user typed and compare it to the stored hash. If they match, the password is correct. You never see or store the original.

---

## Why bcrypt — Not hashlib

Python's built-in `hashlib` is fast. Fast is bad for passwords.

Fast hashing means an attacker can try billions of password guesses per second. bcrypt is intentionally slow — it is designed to take time. This makes brute force attacks computationally expensive.

bcrypt also adds a random **salt** to every password before hashing. This means the same password hashes differently every time, so two users with the same password have different hashes in your database.

| Algorithm | Speed | Safe for Passwords |
|---|---|---|
| hashlib (MD5, SHA256) | Very fast | No |
| bcrypt | Intentionally slow | Yes |

---

## utils.py — hash_password and verify_password

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
```

| Piece | What It Does |
|---|---|
| `CryptContext` | Initialized at module level — shared by both functions |
| `schemes=["bcrypt"]` | Tells passlib to use the bcrypt algorithm |
| `deprecated="auto"` | Handles old hash formats automatically during future migrations |
| `hash_password()` | Returns a bcrypt hash string starting with `$2b$` |
| `verify_password()` | Returns `True` if passwords match, `False` if not |

> `pwd_context` must be at module level — outside the functions. Both functions share it. If you define it inside a function it gets recreated on every call.

---

## User Model — app/models/users.py

SQLAlchemy models represent database tables. They must inherit from `Base`, not from Pydantic's `BaseModel`.

```python
from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
```

| Column | Why |
|---|---|
| `email` with `unique=True` | Enforced at the database level — no two users can share an email |
| `nullable=False` | Email and password are required — database rejects empty values |
| `is_active` | Defaults to True — useful later for banning or soft-deleting users |
| `password` | Stores the bcrypt hash — never the plain text password |

> **Common mistake:** inheriting from `BaseModel` instead of `Base`. `BaseModel` is Pydantic — for schemas. `Base` is SQLAlchemy — for database tables. They are completely different.

---

## User Schemas — app/schemas/users.py

Two separate schemas for the same resource. One for input, one for output.

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True
```

| Schema | Purpose |
|---|---|
| `UserCreate` | What the client sends — email and password |
| `UserResponse` | What the API returns — id, email, is_active. No password. Ever. |

> `from_attributes = True` tells Pydantic to read data from a SQLAlchemy object instead of a plain dict. Without this, FastAPI cannot serialize the response.

> **Rule:** never include the password field in any response schema. Not even as a hashed value. The client has no reason to receive it.

---

## CRUD Layer — app/crud/users.py

```python
from sqlalchemy.orm import Session
from app.models.users import User
from app.schemas.users import UserCreate

def get_user_by_email(email: str, db: Session):
    return db.query(User).filter(User.email == email).first()

def create_user(user: UserCreate, db: Session):
    new_user = User(email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
```

| Function | What It Does |
|---|---|
| `get_user_by_email` | Queries by email — returns the user object or `None` |
| `User(email=..., password=...)` | Creates a SQLAlchemy model instance — not a Pydantic object |
| `db.add()` | Stages the new record |
| `db.commit()` | Writes it to the database permanently |
| `db.refresh()` | Reloads the object from DB — this is how you get the auto-generated `id` back |

> **Common mistake:** passing the Pydantic schema object directly to `db.add()`. SQLAlchemy does not know what a Pydantic object is. Always create a SQLAlchemy model instance first.

---

## Register Endpoint — app/routers/users.py

```python
from fastapi import APIRouter, Depends, HTTPException
from app.database import sessionLocal
from sqlalchemy.orm import Session
from app.utils import hash_password
from app.schemas.users import UserCreate, UserResponse
from app.crud.users import get_user_by_email, create_user

router = APIRouter(prefix='/users', tags=['users'])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post('/register', response_model=UserResponse)
def registration(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(user.email, db):
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = hash_password(user.password)
    new_user = create_user(user, db)
    return new_user
```

### What happens step by step on POST /users/register

1. FastAPI receives the request body and validates it against `UserCreate`
2. `get_user_by_email` checks if the email already exists in the database
3. If it exists — raise `HTTPException` with status 400 and stop
4. Hash the password using `hash_password()` from `utils.py`
5. `create_user` saves the new user to the database
6. FastAPI serializes the response through `UserResponse` — password field is stripped

---

## Duplicate Email Handling

```python
if get_user_by_email(user.email, db):
    raise HTTPException(status_code=400, detail="Email already registered")
```

`get_user_by_email` returns either a user object or `None`.

- If it returns a user object — the email exists — raise 400 and stop
- If it returns `None` — the email is new — continue with registration

The `unique=True` constraint on the database column would also prevent duplicates, but it throws a database-level error which is harder to handle cleanly. Always check at the application level first and return a proper error message.

---

## main.py

```python
from fastapi import FastAPI
from app.models.users import User
from app.database import Base, engine
from app.routers.users import router as user_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(user_router)
```

> Import the `User` model before calling `create_all` — SQLAlchemy needs to know the model exists to create its table.

---

## Common Mistakes Made

| Mistake | Fix |
|---|---|
| `BaseModel` instead of `Base` for SQLAlchemy model | `Base` is SQLAlchemy. `BaseModel` is Pydantic. Never mix them. |
| `pwd_context = None` | Always initialize with `CryptContext(...)` — you cannot call methods on `None` |
| `details` instead of `detail` in HTTPException | One letter difference — FastAPI silently ignores the wrong key |
| Passing Pydantic object to `db.add()` | Create a SQLAlchemy `User(...)` instance first |
| Missing `app.` prefix in imports | All files inside the `app/` folder need `from app.something import ...` |
| Calling `create_all` twice in `main.py` | Only needs to run once at startup |
| Returning password in response schema | Remove the password field from `UserResponse` entirely |

---

## Summary

| File | What It Does |
|---|---|
| `app/utils.py` | `hash_password()` and `verify_password()` using bcrypt |
| `app/models/users.py` | User table — id, email, hashed password, is_active |
| `app/schemas/users.py` | `UserCreate` (input) and `UserResponse` (output, no password) |
| `app/crud/users.py` | `get_user_by_email` and `create_user` database functions |
| `app/routers/users.py` | `POST /users/register` endpoint |
| `main.py` | Creates app, registers user router, creates tables |

---

## What Was Built

- `utils.py` with `hash_password()` and `verify_password()` using passlib and bcrypt
- `User` SQLAlchemy model with hashed password field and unique email constraint
- `UserCreate` schema for incoming registration data
- `UserResponse` schema that returns id, email, is_active — never the password
- `get_user_by_email` CRUD function for duplicate email checking
- `create_user` CRUD function using the standard add → commit → refresh pattern
- `POST /users/register` endpoint with duplicate email handling and password hashing
- Tested in Swagger — successful registration returns user without password, duplicate email returns 400