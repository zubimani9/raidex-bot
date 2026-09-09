import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler

from telegram import Update
from bot import build_application

_app = None
_lock = asyncio.Lock()

async def handle_update(body):
    global _app
    async with _lock:
        if _app is None:
            _app = build_application()
            await _app.initialize()
        update = Update.de_json(body, _app.bot)
        await _app.process_update(update)

class handler(BaseHTTPRequestHandler):
    def reply(self, code, body):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply(200, '{"ok":true,"service":"RaiDEX Telegram Bot"}')

    def do_POST(self):
        secret = os.getenv("WEBHOOK_SECRET", "")
        if secret and self.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
            self.reply(403, '{"ok":false,"error":"forbidden"}')
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n).decode())
            asyncio.run(handle_update(body))
            self.reply(200, '{"ok":true}')
        except Exception as e:
            print("Webhook error:", repr(e))
            self.reply(500, '{"ok":false}')
