# RaiDEX Telegram Bot

Group raid tasks, Telegram Stars PRO, affiliate links, and the RaiDEX Mini App.

## GitHub files to edit

| File | Action |
|---|---|
| `bot.py` | Replace entire file |
| `database.py` | Replace entire file |
| `README.md` | Replace entire file |
| `requirements.txt` | Keep as-is |
| `api/index.py` | Keep as-is (Vercel webhook) |
| `vercel.json` | Keep as-is |

Do not create a second `index.py`.

## Commands

- `/start` private welcome + referral capture
- `/raid <x_link>` group admin starts a task (bot must be admin)
- `/stop` group admin stops the raid
- `/setmedia` reply to photo/GIF/video to save default raid media
- `/clearmedia` remove default media
- `/leaderboard` check-ins for the current group raid
- `/plans` or `/pro` Telegram Stars checkout (private chat)
- `/affiliate` referral link and Stars balance
- `/profile`

Free raid target: 10 likes, 5 comments, 3 reposts.

PRO Stars:
- 750 = 7 days
- 1500 = 15 days
- 2500 = 30 days

Affiliate: `https://t.me/YOUR_BOT?start=refYOUR_ID` — 20% of referred PRO Stars.

This bot posts a task card. It does not like, comment, or repost on X.

## Environment variables

- `BOT_TOKEN` required
- `BOT_USERNAME` example `RaiDEX_RadarBot`
- `RAIDEX_DB_PATH` PythonAnywhere: `/home/YOURUSER/raidex.db`
- `MINI_APP_URL` optional
- `WEBHOOK_SECRET` optional for Vercel
- `AFF_PCT` optional, default `0.20`

## BotFather

1. Enable Stars / digital goods payments.
2. Disable Group Privacy: `/setprivacy` → Disable, so group commands work.
3. `/setcommands`
