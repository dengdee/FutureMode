# Database migrations

Run migration commands from `backend/` after setting `DATABASE_URL` in `.env`:

```cmd
uv run alembic upgrade head
uv run alembic current
```

The initial migration is intentionally empty. Business tables are added in later backend steps.
