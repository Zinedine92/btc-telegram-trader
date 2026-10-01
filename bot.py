Create bot.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [
            InlineKeyboardButton("⛔ STOP BOT", callback_data="stop")
        ],
    ]

    await update.message.reply_text(
        "🚀 BTC TRADER V1\n\n"
        "Mode: DEMO\n"
        "Pair: BTCUSDT\n"
        "Leverage: 20x\n"
        "Risk: 0.5%\n"
        "RR: 1:2\n\n"
        "اختار العملية:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    responses = {
        "price": (
            "📊 BTC Price\n\n"
            "Demo mode — price feed not connected yet."
        ),

        "settings": (
            "⚙️ Settings\n\n"
            "Leverage: 20x\n"
            "Risk: 0.5%\n"
            "RR: 1:2"
        ),

        "long": (
            "🟢 LONG\n\n"
            "Demo order selected.\n"
            "Execution engine will be added next."
        ),

        "short": (
            "🔴 SHORT\n\n"
            "Demo order selected.\n"
            "Execution engine will be added next."
        ),

        "trades": (
            "📋 Open Trades\n\n"
            "No open trades."
        ),

        "history": (
            "📈 History\n\n"
            "No trades yet."
        ),

        "stop": (
            "⛔ Trading stopped.\n\n"
            "No real orders are connected."
        ),
    }

    await query.edit_message_text(
        responses.get(query.data, "Unknown command.")
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("BTC Telegram Bot V1 started...")

    app.run_polling()


if __name__ == "__main__":
    main()
