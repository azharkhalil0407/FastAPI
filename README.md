# FastAPI Learning

## CRUD API with in-memory storage
Built a fully functional CRUD API using FastAPI and Pydantic with in-memory dictionary storage.
Covers routing, path and query parameters, request validation, HTTP status codes, and error handling.

## Database integration with SQLAlchemy
Connected FastAPI to a persistent SQLite database using SQLAlchemy.
Covers engine setup, session management, dependency injection, Pydantic vs SQLAlchemy models and full CRUD with real data persistence.

## Project restructure, environment variables, and production-grade architecture
Restructured the project into a production-grade folder layout following the Single Responsibility Principle.
Covers environment variables with `.env`, Pydantic settings validation at startup, `.gitignore` best practices, separated schemas, CRUD layer, router layer with `APIRouter`, dependency injection, and an introduction to Alembic for database migrations.
