# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Backend API for "Plataforma de Revisão Inteligente" — a study review scheduling platform built with FastAPI + MySQL. Students register subjects (disciplinas), log studied topics, and receive scheduled reviews. Professors monitor progress via dashboard.

## Commands

```bash
# Activate virtual environment
.venv/Scripts/activate        # Windows
source .venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --reload

# No test framework is configured yet
```

## Environment

Requires a `.env` file in the project root with:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — MySQL connection
- `SECRET_KEY`, `ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT config
- `CORS_ORIGINS` — comma-separated allowed origins (defaults to `http://localhost:4200`)

Database is MySQL via PyMySQL driver. Never use SQLite.

## Architecture

**Layered structure:** Routers → Services → Models, with Pydantic schemas for validation.

- **`main.py`** — App entry point. Creates tables via `Base.metadata.create_all()`, configures CORS and rate limiting (slowapi), mounts routers.
- **`app/core/config.py`** — `Settings` class using pydantic-settings, loads from `.env`.
- **`app/database/connection.py`** — SQLAlchemy engine, `SessionLocal`, `Base`, and `get_db()` dependency.
- **`app/models/`** — SQLAlchemy ORM models: `User` (with `RoleEnum`), `BlacklistedToken`, `Disciplina`, `Topico`.
- **`app/schemas/`** — Pydantic request/response schemas per domain entity.
- **`app/services/`** — Business logic. `auth.py` exports key dependencies: `get_current_user` and `require_aluno`.
- **`app/routers/`** — FastAPI route handlers organized by domain: `auth`, `disciplinas`, `topicos`.

**Auth flow:** HTTPBearer token → `get_current_user` decodes JWT and checks blacklist → returns `User` object. `require_aluno` further restricts to `aluno` role.

**Authorization model:** Two roles — `aluno` (default on register) and `professor` (promoted manually via DB). Alunos own their data; professors have read-only access to all data.

**Relationships:** User → Disciplinas → Topicos, all with cascade delete.

## Conventions

- All code uses **Portuguese naming** for domain terms (usuario, disciplina, topico, senha, etc.)
- Git workflow: develop on `dev` branch, merge to `main` for production
- **Never** add `Co-Authored-By` or Claude attribution in commits
- Router prefix pattern: `/auth/*`, `/disciplinas/*`, `/disciplinas/{id}/topicos/*`
- Dependencies are injected via FastAPI's `Depends()` — follow existing patterns in `services/auth.py`
