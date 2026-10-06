"""Telegram interface for the BTC/USDT trading bot.

This version is DEMO/analysis-only. It does not place exchange orders.
Secrets must be provided through environment variables and never committed.
"""

import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes


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

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("BTC Telegram Bot V1 started in DEMO mode...")
    app.run_polling()


if __name__ == "__main__":
    main()
