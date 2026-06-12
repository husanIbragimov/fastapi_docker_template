# Contributing

## Getting Started

```bash
git clone https://github.com/husanIbragimov/fastapi_docker_template.git
cd fastapi_docker_template
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Workflow

1. Fork the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Make your changes following the conventions below.
3. Run the full check suite locally (see below) — CI must pass.
4. Open a pull request against `main` with a clear description of what and why.

## Branch Naming

| Prefix | Use |
|---|---|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `refactor/` | Code change with no behaviour change |
| `docs/` | Documentation only |
| `test/` | Tests only |
| `chore/` | Tooling, deps, config |

## Code Style

This project uses **Ruff**, **Black**, and **isort**. Pre-commit runs them automatically on every commit. To run manually:

```bash
ruff check . --fix
black .
isort .
mypy app/
```

Key conventions:
- Strict layered architecture: **Router → Service → Repository → DB**. Business logic belongs in services, not routers or repositories.
- No comments that describe *what* the code does — only *why* when the reason is non-obvious.
- New cached service methods: apply `@cache(ttl=300, namespace="your_ns")` on the service, not the router.
- All responses use `success_response()` / `error_response()` from `app/core/responses.py`.

## Adding a New Module

1. **Model** — `app/models/your_model.py` extending `Base` + `TimestampMixin`
2. **Repository** — `app/repositories/your_model.py` extending `BaseRepository[YourModel]`
3. **Schema** — `app/schemas/your_model.py` with Pydantic v2 models (`ConfigDict(from_attributes=True)`)
4. **Service** — `app/services/your_model.py` injecting the repository
5. **Router** — `app/api/v1/your_model.py`, registered in `app/api/v1/router.py`
6. **Migration** — `alembic revision --autogenerate -m "add your_model table"`
7. **Tests** — `tests/test_your_model.py`

## Tests

PostgreSQL and Redis must be running. The suite uses a separate `test_app_db` database.

```bash
# Create test database (first time only)
docker exec <postgres-container> psql -U app_user -d app_db -c "CREATE DATABASE test_app_db;"

# Run all tests
pytest tests/ -v

# Run a single file
pytest tests/test_auth.py -v
```

- Each test gets its own `db_session` that rolls back after the test — no manual cleanup needed.
- Use `unique_email()` / `unique_username()` from `tests/factories.py` whenever you create users to avoid unique constraint collisions.
- Tests and fixtures share a single session-scoped event loop (`asyncio_default_test_loop_scope = "session"` in `pyproject.toml`) — required for Python 3.13+ compatibility with asyncpg.

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <short summary>

Optional body explaining why, not what.
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

## Pull Request Checklist

- [ ] `ruff`, `black`, `isort`, and `mypy` pass with no errors
- [ ] All existing tests pass
- [ ] New behaviour is covered by tests
- [ ] New endpoints are documented (docstring or updated README)
- [ ] Migration generated if models changed (`alembic revision --autogenerate`)

## Reporting Issues

Open a GitHub issue with:
- A minimal reproduction (endpoint + request body, or failing test)
- Expected vs actual behaviour
- Python version and OS
