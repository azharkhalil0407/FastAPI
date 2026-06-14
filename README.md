# Backend_development

## CRUD API with in-memory storage
Built a fully functional CRUD API using FastAPI and Pydantic with in-memory dictionary storage.
Covers routing, path and query parameters, request validation, HTTP status codes, and error handling.

## Database integration with SQLAlchemy
Connected FastAPI to a persistent SQLite database using SQLAlchemy.
Covers engine setup, session management, dependency injection, Pydantic vs SQLAlchemy models and full CRUD with real data persistence.

## Project restructure, environment variables, and production-grade architecture
Restructured the project into a production-grade folder layout following the Single Responsibility Principle.
Covers environment variables with `.env`, Pydantic settings validation at startup, `.gitignore` best practices, separated schemas, CRUD layer, router layer with `APIRouter`, dependency injection, and an introduction to Alembic for database migrations.

## Password hashing and user registration
Built a full user registration flow with secure password hashing using bcrypt via passlib.
Covers why plain text storage is dangerous, how bcrypt works, `utils.py` with hash and verify functions, User SQLAlchemy model, separate `UserCreate` and `UserResponse` Pydantic schemas, CRUD layer for users, and a `POST /users/register` endpoint that validates input, checks for duplicate emails, hashes the password, and returns a safe response.

## JWT Authentication and protected routes
Built a stateless authentication system using JSON Web Tokens (JWT).
Covers how JWT solves HTTP statelessness, token structure (header, payload, signature), signing and verifying tokens with a `SECRET_KEY`, token expiry, `OAuth2PasswordRequestForm` for parsing login form data, `OAuth2PasswordBearer` for extracting tokens from the `Authorization` header, `create_access_token` and `get_current_user` utilities, a `POST /users/login` endpoint, and a protected `GET /users/me` endpoint using `Depends`. Also covers circular import resolution by isolating `get_db` into `dependencies.py`.

## SQLite to PostgreSQL migration
Migrated the database layer from SQLite to PostgreSQL for production-readiness.
Covers why SQLite breaks under FastAPI's multi-threading, installing and running PostgreSQL locally, `psql` basics, Python's `psycopg2` adapter, updating the `DATABASE_URL` and engine config, and forcing table creation by explicitly importing all models at startup.

## Foreign keys and relationships
Introduced relational integrity between the `users` and `products` tables using PostgreSQL-enforced foreign keys.
Covers dangling reference problems, `ondelete` behavior (`RESTRICT`, `CASCADE`, `SET NULL`), correct `ForeignKey` syntax referencing table names not class names, `relationship()` as a Python-only navigation shortcut, `back_populates` for two-way in-memory sync, `create_all` limitations and the development workaround using `DROP TABLE ... CASCADE`, and resolving circular imports with `from __future__ import annotations`.

## Relationships extended, query patterns, and error handling
Extended the relational layer with user-scoped queries, eager loading, and production-grade error handling.
Covers the N+1 problem and fixing it with `joinedload()`, `joinedload` vs `selectinload`, user-scoped `GET /products/` using the authenticated user's id, `IntegrityError` handling with `db.rollback()` and `raise` in the CRUD layer, global exception handlers in `main.py` for consistent error response shapes across `RequestValidationError` and `HTTPException`, Pydantic `Field` validators (`gt`, `ge`, `min_length`, `pattern`), the security fix of removing `user_id` from the request schema and pulling it from the JWT token instead, and the architectural difference between `HTTPException` and custom domain exceptions.

## Task Manager API — full project build
Built a complete production-structured Task Manager API consolidating all prior concepts into a single deployable project.
Covers project scaffolding following single responsibility principle, `TaskStatus` as a `str` enum for JSON-safe serialization, partial update pattern with all-optional `TaskUpdate` schema, pagination with `offset = (page - 1) * size`, case-insensitive title search using `ilike`, ownership checks with 404-before-403 ordering, `user_id` injected from JWT token never from the client, global exception handlers for consistent error shapes, and explicit model imports in `main.py` to ensure `create_all` creates all tables. Live at [github.com/azharkhalil0407/task-manager-api](https://github.com/azharkhalil0407/task-manager-api).

## Testing FastAPI applications with pytest
Introduced automated testing with pytest and FastAPI's `TestClient`, replacing manual `/docs` verification with a repeatable test suite.
Covers why production databases must not be used in tests, `conftest.py` as the shared fixture home, `scope="function"` for full test isolation, `dependency_overrides` to swap `get_db` for a test session without touching application code, file-based SQLite (`test.db`) over `:memory:` for shared connection state, auth fixture chaining (`registered_user` → `auth_token` → `auth_headers`), 404-before-403 ownership test pattern using two separate users, and pinning `bcrypt==4.0.1` for `passlib` compatibility. 11 tests across `test_auth.py` and `test_tasks.py`, all passing.
