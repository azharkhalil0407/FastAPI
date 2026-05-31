# Backend_dev_Learning

## CRUD API with in-memory storage
Built a fully functional CRUD API using FastAPI and Pydantic with in-memory dictionary storage.
Covers routing, path and query parameters, request validation, HTTP status codes, and error handling.

## Database integration with SQLAlchemy
Connected FastAPI to a persistent SQLite database using SQLAlchemy.
Covers engine setup, session management, dependency injection, Pydantic vs SQLAlchemy models and full CRUD with real data persistence.

## Project restructure, environment variables, and production-grade architecture
Restructured the project into a production-grade folder layout following the Single Responsibility Principle.
Covers environment variables with `.env`, Pydantic settings validation at startup, `.gitignore` best practices, separated schemas, CRUD layer, router layer with `APIRouter`, dependency injection, and an introduction to Alembic for database migrations.
<<<<<<< HEAD
=======

## Password hashing and user registration
Built a full user registration flow with secure password hashing using bcrypt via passlib.
Covers why plain text storage is dangerous, how bcrypt works, `utils.py` with hash and verify functions, User SQLAlchemy model, separate `UserCreate` and `UserResponse` Pydantic schemas, CRUD layer for users, and a `POST /users/register` endpoint that validates input, checks for duplicate emails, hashes the password, and returns a safe response.
>>>>>>> d18821a (password hashing and user registration)
