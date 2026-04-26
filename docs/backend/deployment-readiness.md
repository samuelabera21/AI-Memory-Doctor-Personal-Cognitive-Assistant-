# Deployment Readiness Checklist

## Current Status

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Run backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Then in a second terminal run frontend:

cd ~/Desktop/AI/ai-memory-doctor/frontend
npm run dev
S

This backend is suitable for deployment in a small-to-medium environment after environment variables are configured.

For Render deployment, the backend is ready when the environment variables below are set in the Render dashboard.

## What Is Ready

- Auth with JWT and hashed passwords
- Multi-user memory isolation by user_id
- Versioned update policy with active row filtering
- Soft delete and admin-only hard delete
- Hybrid search and temporal reasoning
- Evaluation export endpoint (JSON + CSV)
- CORS and trusted host middleware
- Liveness and readiness health checks
- Dockerfile for container deployment

## Health Endpoints

- GET /health/live
- GET /health/ready

## Required Environment Variables

- APP_NAME
- ENVIRONMENT
- DEBUG
- DATABASE_URL
- JWT_SECRET_KEY
- JWT_ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES
- BACKEND_PORT
- WORKERS
- CORS_ORIGINS
- ALLOWED_HOSTS
- TIMEZONE
- DATE_FORMAT
- LANGUAGE
- ADMIN_EMAILS
- EMBEDDING_MODEL_NAME
- LLM_PROVIDER
- LLM_API_KEY
- LLM_MODEL

## Render-Specific Checklist

- Set service type to Web Service.
- Ensure the app listens on `0.0.0.0:$PORT` (already handled in Docker CMD).
- Set `ALLOWED_HOSTS` to include your Render domain, for example:
	- `localhost,127.0.0.1,*.onrender.com`
- Set `CORS_ORIGINS` to include your frontend URL.
- If using SQLite, mount a persistent disk and point `DATABASE_URL` to that path.
- Prefer PostgreSQL for production reliability and scaling.

## Production Recommendations

- Use PostgreSQL instead of SQLite for multi-instance production.
- Store secrets in platform secret manager.
- Add centralized logging and metrics collection.
- Add API rate limiting and abuse protection.
- Add alembic migration workflow for schema evolution.

## Container Run Example

```bash
docker build -t ai-memory-doctor-backend -f backend/Dockerfile .
docker run --rm -p 8000:8000 --env-file .env.example ai-memory-doctor-backend
```
