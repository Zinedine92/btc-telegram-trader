"""Telegram interface for the BTC/USDT trading bot.

This version is DEMO/analysis-only. It does not place exchange orders.
Secrets must be provided through environment variables and never committed.
"""

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal HTTP health endpoint for Render Web Service."""

    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b'{"status":"ok","mode":"demo","execution":"disabled"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Health server listening on 0.0.0.0:{port}")
    return server


def build_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 BTC Price", callback_data="price"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("🟢 LONG", callback_data="long"),
            InlineKeyboardButton("🔴 SHORT", callback_data="short"),
        ],
        [
            InlineKeyboardButton("📋 Open Trades", callback_data="trades"),
            InlineKeyboardButton("📈 History", callback_data="history"),
        ],
        [InlineKeyboardButton("⛔ STOP BOT", callback_data="stop")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 BTC TRADER V1\n\n"
        "Mode: DEMO / ANALYSIS ONLY\n"
        "Pair: BTCUSDT\n"
        "Leverage limit: 20x\n"
        "Risk limit: 0.5%\n"
        "Minimum RR: 1:2\n\n"
        "لا توجد أوامر حقيقية متصلة بالمنصة.\n"
        "اختار العملية:",
        reply_markup=build_keyboard(),
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 BOT STATUS\n\n"
        "Telegram: ONLINE\n"
        "Mode: DEMO / ANALYSIS ONLY\n"
        "Execution: DISABLED\n"
        "Risk Engine: REQUIRED BEFORE EXECUTION"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    responses = {
        "price": "📊 BTC Price\n\nDemo mode — price feed not connected yet.",
        "settings": (
            "⚙️ Settings\n\n"
            "Leverage hard limit: 20x\n"
            "Risk per trade: 0.5%\n"
            "Minimum RR: 1:2"
        ),
        "long": (
            "🟢 LONG selected\n\n"
            "DEMO ONLY — no real order was sent.\n"
            "Signal validation + Risk Engine must pass before any future execution."
        ),
        "short": (
            "🔴 SHORT selected\n\n"
            "DEMO ONLY — no real order was sent.\n"
            "Signal validation + Risk Engine must pass before any future execution."
        ),
        "trades": "📋 Open Trades\n\nNo real open trades.",
        "history": "📈 History\n\nNo trades yet.",
        "stop": "⛔ Trading stopped.\n\nReal execution is disabled.",
    }

    await query.edit_message_text(
        responses.get(query.data, "Unknown command.")
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")

    start_health_server()

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("BTC Telegram Bot V1 started in DEMO mode...")
    app.run_polling()


if __name__ == "__main__":
    main()
