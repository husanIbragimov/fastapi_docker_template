# FastAPI Docker Template

Production-ready FastAPI boilerplate with async PostgreSQL, Redis caching, JWT auth, background tasks, structured logging, and a full test suite.

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115+ |
| Database | PostgreSQL 16 + SQLAlchemy 2.x async + asyncpg |
| Migrations | Alembic |
| Cache | Redis 7 + redis-py async |
| Auth | PyJWT (access + refresh tokens with rotation) |
| Background tasks | FastAPI `BackgroundTasks` + arq worker |
| Logging | structlog (JSON in prod, console in dev) |
| Validation | Pydantic v2 |
| Testing | pytest-asyncio + httpx |
| Containers | Docker + Docker Compose |

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── health.py          # GET /health, /health/db, /health/redis
│   │   └── v1/
│   │       ├── auth.py        # register, login, refresh, logout, me
│   │       └── users.py       # user CRUD with pagination
│   ├── auth/
│   │   ├── jwt.py             # access + refresh token creation/decode
│   │   └── password.py        # bcrypt hash/verify
│   ├── background/
│   │   ├── tasks.py           # FastAPI BackgroundTasks helpers
│   │   └── worker.py          # arq WorkerSettings + task functions
│   ├── cache/
│   │   ├── backend.py         # Redis client + get/set/delete helpers
│   │   └── decorator.py       # @cache(ttl, namespace) decorator
│   ├── core/
│   │   ├── config.py          # Pydantic Settings (env-driven)
│   │   ├── exceptions.py      # AppException hierarchy
│   │   ├── logging_conf.py    # structlog setup
│   │   └── responses.py       # unified response format + exception handlers
│   ├── db/
│   │   ├── base.py            # DeclarativeBase
│   │   ├── mixins.py          # TimestampMixin
│   │   └── session.py         # async engine + get_db dependency
│   ├── dependencies/
│   │   ├── auth.py            # get_current_user, require_superuser
│   │   └── pagination.py      # pagination_params dependency
│   ├── middleware/
│   │   ├── logging.py         # request logging (method, path, status, duration)
│   │   └── request_id.py      # X-Request-ID injection
│   ├── models/user.py
│   ├── repositories/
│   │   ├── base.py            # generic BaseRepository[T]
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── common.py          # PaginatedResponse, SuccessResponse
│   │   └── user.py
│   ├── services/user.py       # business logic, token rotation, @cache
│   ├── utils/pagination.py
│   └── main.py                # app factory
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml     # dev (hot reload)
│   └── docker-compose.prod.yml
├── migrations/                # Alembic
├── scripts/
│   ├── migrate.sh
│   ├── start.sh
│   └── worker.sh
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── test_auth.py
│   ├── test_health.py
│   └── test_users.py
├── main.py                    # uvicorn entrypoint
└── pyproject.toml
```

## Quick Start (local)

**Prerequisites:** Python 3.13+, Docker

```bash
# 1. Clone and create virtualenv
git clone https://github.com/husanIbragimov/fastapi_docker_template.git
cd fastapi_docker_template
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# 2. Start PostgreSQL and Redis
docker compose -f docker/docker-compose.yml up -d postgres redis

# 3. Configure environment
cp .env.example .env
# Edit .env — set REDIS_PORT to match your host binding (check `docker ps`)

# 4. Run migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Quick Start (Docker)

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts the API (with hot reload), PostgreSQL, and Redis together.

## Environment Variables

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` / `production` |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_NAME` | `app_db` | Database name |
| `DB_USER` | `app_user` | Database user |
| `DB_PASSWORD` | `app_password` | Database password |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `JWT_SECRET_KEY` | *(insecure default)* | Change in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `LOG_FORMAT` | `console` | `console` (dev) or `json` (prod) |

## API Endpoints

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create account |
| POST | `/api/v1/auth/login` | — | Get access + refresh tokens |
| POST | `/api/v1/auth/refresh` | — | Rotate refresh token |
| POST | `/api/v1/auth/logout` | — | Revoke refresh token |
| GET | `/api/v1/auth/me` | Bearer | Current user |

### Users

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/users` | Superuser | List users (paginated) |
| GET | `/api/v1/users/me` | Bearer | Own profile |
| GET | `/api/v1/users/{id}` | Bearer | Get user by ID |
| PATCH | `/api/v1/users/{id}` | Bearer | Update user |
| DELETE | `/api/v1/users/{id}` | Bearer | Delete user |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service status |
| GET | `/health/db` | PostgreSQL connectivity |
| GET | `/health/redis` | Redis connectivity |

All responses follow a unified envelope:

```json
{ "success": true, "message": "...", "data": {} }
{ "success": false, "message": "...", "error_code": "..." }
```

## Running Tests

PostgreSQL and Redis must be running. The test suite uses a separate `test_app_db` database.

```bash
# Create test database (first time only)
docker exec <postgres-container> psql -U app_user -d app_db -c "CREATE DATABASE test_app_db;"

# Run tests
pytest tests/ -v
```

26 tests cover auth flows, token rotation, user CRUD, pagination, and health checks.

## Background Worker

```bash
# Start the arq worker (separate terminal)
arq app.background.worker.WorkerSettings
```

Tasks defined in `app/background/worker.py`: `send_email_task`, `process_notification_task`, `generate_report_task`.

## Architecture

Strict layered architecture — each layer has one responsibility and dependencies flow downward only:

```
Router → Service → Repository → Database
                ↘ Cache (Redis)
```

- **Router** — HTTP concerns only (request parsing, response formatting)
- **Service** — business logic, orchestrates repositories and cache
- **Repository** — all database queries via SQLAlchemy async sessions
- **Cache** — apply `@cache(ttl=300, namespace="ns")` to any async service method

## Code Quality

```bash
ruff check .          # lint
black --check .       # format check
isort --check-only .  # import order
mypy app/             # type check
pre-commit run --all-files
```

CI runs lint, tests, and migration check on every push via `.github/workflows/ci.yml`.
