# team-tracker

## Production Deployment

This app can be run in production with Docker and Docker Compose using a MySQL database.

1. Copy the example environment file and fill in values:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` with valid production values, including reCAPTCHA keys:

```
RECAPTCHA_SITE_KEY=...
RECAPTCHA_SECRET_KEY=...
```

2. Start services:

```bash
docker-compose --env-file .env.production up --build
```

For systems with old Compose v2 behavior, use:

```bash
docker compose --env-file .env.production up --build
```

The web service runs on port `7050` in the sample compose setup.
