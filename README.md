# RaiDEX — Vercel webhook version

## Required Vercel environment variables

- `BOT_TOKEN` — Telegram bot token
- `MINI_APP_URL` — optional, defaults to the GitHub Pages Mini App URL
- `WEBHOOK_SECRET` — optional secret for Telegram webhook requests

## File structure

```text
api/
  index.py
bot.py
database.py
requirements.txt
vercel.json
```

Do not keep a second `index.py`, `index-1.py`, or `api/index-1.py`.

After deployment, the Telegram webhook endpoint is:

`https://YOUR-DOMAIN/api/index.py`

SQLite is stored under `/tmp` on Vercel and is ephemeral. For permanent production user/payment data, use an external database.
