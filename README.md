# FastAPI Starter

A clean, minimal FastAPI starter template with async PostgreSQL, type checking, and Docker support.

---
## Tech Stack:

- **FastAPI** - async web framework
- **PostgreSQL** - main database
- **SQLModel** - ORM with Pydantic-style models
- **Alembic** - database migrations
- **Pydantic** - data validation
- **UV** - dependency management
- **Mypy, Ruff** - static analysis & linting
- **Docker Compose** - local PostgreSQL deployment

---
## Getting Started

### 1. Create your own repository

Instead of cloning directly, click the “Use this template” button on the GitHub page of this project, then select “Create a new repository”.
This gives you your own copy, independent of the original.

After creating your repo, clone it:

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Install dependencies

Make sure you have **uv** installed.
Then install project dependencies:

```bash
uv sync
```

### 3. Configure environment

Create `.env` files based on `.env.example` files located in the root and in `local/postgres_db/`.

```bash
cp .env.example .env
cp local/postgres_db/.env.example local/postgres_db/.env
```

### 4. Run local PostgreSQL via Docker

Make sure you have Docker and Docker Compose installed.

```bash
docker compose -f local/postgres_db/docker-compose.yml up -d
```

This starts a local PostgreSQL database.

### 5. Run database migrations

After creating or modifying models, generate and apply migrations:

```bash
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```

### 6. Run checks before commit

```bash
ruff check --fix
mypy app
```

---

## Recommended Project Structure

```
app/
  ├── __init__.py
  ├── main.py
  ├── settings.py
  ├── database/
  │   ├── __init__.py
  │   ├── engine.py
  │   └── seesion.py
  ├── users/                # example module
  │   ├── __init__.py
  │   ├── model.py
  │   ├── repository.py
  │   ├── service.py
  │   └── router.py
alembic/
local/
  └── postgres_db/
      ├── .env
      └── docker-compose.yml
```

---
## Useful Commands

| Task              | Command                         |
|-------------------|---------------------------------|
| Run app locally   | `uvicorn app.main:app --reload` |
| Start PostgreSQL  | `docker compose up -d`          |
| Run migrations    | `alembic upgrade head`          |
| Lint & type check | `ruff check --fix && mypy app`  |

---
## Notes

* Keep your `.env` files out of version control.
* Use async SQLModel operations for best performance.
* Always run linters and type checkers before committing.
