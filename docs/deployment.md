# Deployment

## Local / Development (Docker Compose)

```bash
docker-compose up
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

## Production (Phase 2)

### Option A: Railway.app (simplest)

1. Push repo to GitHub
2. Create Railway project, add PostgreSQL service
3. Deploy backend service: set `DATABASE_URL` env var from Railway's PostgreSQL URL
4. Deploy dashboard service: set `API_BASE_URL` to backend URL

### Option B: AWS

- **Backend:** ECS Fargate task (multi-stage Dockerfile `target: backend`)
- **Dashboard:** ECS Fargate (target: dashboard) or Streamlit Cloud
- **Database:** RDS PostgreSQL (auto-backup, multi-AZ)
- **Secrets:** AWS Secrets Manager for `DATABASE_URL`

### Environment Variables (Production)

```env
DATABASE_URL=postgresql://user:pass@rds-host:5432/vendorio_db
FASTAPI_ENV=production
LOG_LEVEL=WARNING
SECRET_KEY=<generate with: openssl rand -hex 32>
```

### Healthcheck

The `/health` endpoint is suitable as a container liveness probe.
