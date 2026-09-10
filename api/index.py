import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler

from telegram import Update
from bot import build_application

_app = None

async def handle_update(body):
    global _app
    if _app is None:
        _app = build_application()
        await _app.initialize()
    update = Update.de_json(body, _app.bot)
    await _app.process_update(update)

class handler(BaseHTTPRequestHandler):
    def _reply(self, code, body):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._reply(200, json.dumps({"ok": True, "service": "RaiDEX Telegram Bot"}))

    def do_POST(self):
        secret = os.getenv("WEBHOOK_SECRET", "").strip()
        if secret and self.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
            self._reply(403, json.dumps({"ok": False, "error": "forbidden"}))
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            asyncio.run(handle_update(body))
            self._reply(200, json.dumps({"ok": True}))
        except Exception as exc:
            print("Webhook error:", repr(exc))
            self._reply(500, json.dumps({"ok": False, "error": str(exc)}))

    def log_message(self, fmt, *args):
        print(fmt % args)
