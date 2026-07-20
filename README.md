# ShipTrack: Deployment Tracker API

ShipTrack is a FastAPI-based REST API for tracking software deployments. It records which application was deployed, the deployed version, target environment, deployment status, and supports deployment rollback. The project uses PostgreSQL 16, Docker, SQLAlchemy 2.0, and GitHub Actions for CI/CD.

---

# Features

- Manage applications
- Track deployments
- Rollback to previous successful deployment
- API Key protection for write operations
- Background audit logging
- PostgreSQL database
- Docker & Docker Compose support
- Automated testing with Pytest
- CI/CD with GitHub Actions

---

# Environment Variables

Copy the example environment file before running the project.

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| API_KEY | API key required for POST/PATCH endpoints |
| APP_ENV | Application environment (development/local) |
| LOG_LEVEL | Logging level |

---

# Running the API

Start the API and PostgreSQL:

```bash
docker compose up --build -d
```

Swagger documentation:

```
http://localhost:8000/docs
```

Health endpoint:

```
GET /health
```

---

# API Endpoints

## Applications

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | /applications | Create application |
| GET | /applications | List applications |

## Deployments

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | /deployments | Create deployment |
| GET | /deployments | List deployments |
| POST | /deployments/{deployment_id}/rollback | Rollback deployment |

## Health

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | /health | API & database health check |

---

# Running Tests

Run all tests with coverage inside the API container.

```bash
docker compose exec -T api pytest --cov=app --cov-report=term-missing --cov-fail-under=60
```

Run Ruff:

```bash
docker compose exec -T api ruff check .
```

---

# Nightly Database Backup (Cron)

Add the following line to your crontab:

```cron
0 2 * * * cd /Users/mac/Desktop/abdul-ahad-shiptrack && ./scripts/backup_db.sh >> logs/backup.log 2>&1
```

Cron fields:

- Minute
- Hour
- Day of Month
- Month
- Day of Week

The absolute path and `cd` are required because cron runs from a minimal shell environment and does not automatically execute inside the project directory.

---

# Live Reload

The project uses bind mounts together with FastAPI's reload mode.

After editing files inside the `app/` directory, the API reloads automatically without rebuilding the Docker image.

---

# Docker Hub

Docker image:

https://hub.docker.com/r/abdulahadmujahid/shiptrack

---

# Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- PostgreSQL 16
- Docker
- Docker Compose
- Pytest
- Ruff
- GitHub Actions

---

# Image Size

The final Docker image is below **300 MB**, satisfying the assignment requirement.
