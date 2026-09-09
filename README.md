# RaiDEX — Vercel webhook version

## Required Vercel environment variables
- `BOT_TOKEN` — Telegram bot token
- `MINI_APP_URL` — optional Mini App URL
- `WEBHOOK_SECRET` — optional Telegram webhook secret

## File structure
```text
api/
  index.py
bot.py
database.py
requirements.txt
pyproject.toml
vercel.json
README.md
```

Do not keep a second `index.py`, `index-1.py`, or `api/index-1.py`.

After deployment, use the deployed Vercel function URL shown by Vercel for the Telegram webhook.

Note: SQLite defaults to `/tmp/raidex.db` on Vercel and is ephemeral. For permanent production data, use a hosted database.
