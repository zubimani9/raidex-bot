# RaiDEX — Vercel webhook version

1. Import this repository into Vercel.
2. Add `BOT_TOKEN` as an Environment Variable.
3. Optional: add `MINI_APP_URL`.
4. Recommended: add `WEBHOOK_SECRET`.
5. Deploy.
6. Set Telegram webhook to:
   `https://api.telegram.org/botBOT_TOKEN/setWebhook?url=https://YOUR-DOMAIN/api/index.py&secret_token=WEBHOOK_SECRET`

Important: SQLite on Vercel `/tmp` is ephemeral. PRO/user/payment data is NOT persistent across cold starts/deployments. Use a persistent external database for production payments.
Do not commit your `.env` or bot token.
