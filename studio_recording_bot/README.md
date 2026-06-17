# Telegram bot for a recording studio

Production-oriented aiogram 3 bot for booking recording sessions in a studio.

## What is included

- Python 3.12, aiogram 3, PostgreSQL, SQLAlchemy 2 async, Alembic.
- Client, sound engineer and administrator roles.
- Telegram-only navigation with reply and inline keyboards.
- Booking flow with date, engineer, slot, client data, duration and final confirmation.
- Night booking requests with manual approval.
- Engineer approval/rejection and attendance statuses.
- Referral links, anti-abuse referral accounting and bonus ledger.
- Admin Telegram panel: statistics, bookings, clients, engineers, admins, role management.
- Monthly text + PDF report job.
- Reminder job for clients and engineers.
- Docker, docker-compose, Railway config and `.env` driven settings.

## Quick start locally

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Fill in `BOT_TOKEN`, `DATABASE_URL` and `INITIAL_ADMIN_IDS`.

3. Start PostgreSQL and the bot:

```bash
docker compose up --build
```

4. Apply migrations if you run outside Docker:

```bash
alembic upgrade head
python -m app.main
```

## Railway deploy

1. Create a Railway project.
2. Add a PostgreSQL service.
3. Add these variables to the bot service:

```text
BOT_TOKEN=...
DATABASE_URL=${{Postgres.DATABASE_URL}}
INITIAL_ADMIN_IDS=123456789,987654321
BOT_USERNAME=your_bot_username
TIMEZONE=Asia/Yekaterinburg
```

4. Deploy from GitHub. Railway uses `railway.toml` and the Dockerfile.

The container runs `alembic upgrade head` before starting the bot.

## Important operational notes

- All secrets are read from environment variables.
- The database migration enables PostgreSQL `btree_gist` and adds an exclusion constraint to prevent overlapping active bookings for the same engineer.
- Telegram users are created on first interaction. Referral links use `/start ref_<telegram_id>`.
- The first admins come from `INITIAL_ADMIN_IDS`; additional admins and engineers can be added from the Telegram admin panel.
- The bot uses long polling. For webhook deployments, replace `Dispatcher.start_polling` in `app/main.py`.

## Project structure

```text
app/
  bot/               Telegram routers, keyboards, middlewares
  db/                SQLAlchemy models, session, migrations
  services/          Booking, bonus, stats, report and notification logic
  config.py          Pydantic settings
  main.py            Application entrypoint
```

