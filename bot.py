"""Telegram interface for the BTC/USDT trading bot.

Demo/analysis-only mode. No exchange orders are placed.
"""

import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from binance_balance import get_btc_usdt_balances
from market_data import get_btcusdt_price, get_btcusdt_candles
from strategy import analyze
from risk_gate import evaluate_analysis


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
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
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Health server listening on 0.0.0.0:{port}")


def build_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 BTC Price", callback_data="price"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("🟢 LONG", callback_data="long"),
         InlineKeyboardButton("🔴 SHORT", callback_data="short")],
        [InlineKeyboardButton("📋 Open Trades", callback_data="trades"),
         InlineKeyboardButton("📈 History", callback_data="history")],
        [InlineKeyboardButton("⛔ STOP BOT", callback_data="stop")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 BTC TRADER V1\n\n"
        "Mode: DEMO / ANALYSIS ONLY\n"
        "Pair: BTCUSDT\n"
        "Leverage limit: 20x\n"
        "Risk limit: 0.5%\n"
        "Minimum RR: 1:2\n\n"
        "لا توجد أوامر حقيقية متصلة بالمنصة.",
        reply_markup=build_keyboard(),
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 BOT STATUS\n\n"
        "Telegram: ONLINE\n"
        "Mode: DEMO / ANALYSIS ONLY\n"
        "Market Data: READ-ONLY\n"
        "Execution: DISABLED\n"
        "Risk Engine: REQUIRED BEFORE EXECUTION"
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balances = get_btc_usdt_balances()
        btc = balances.get("BTC", {"free": 0.0, "locked": 0.0})
        usdt = balances.get("USDT", {"free": 0.0, "locked": 0.0})
        await update.message.reply_text(
            "💰 BINANCE BALANCE\n\n"
            f"BTC\nFree: {btc['free']:.8f}\nLocked: {btc['locked']:.8f}\n\n"
            f"USDT\nFree: {usdt['free']:.2f}\nLocked: {usdt['locked']:.2f}\n\n"
            "🔒 READ-ONLY — no orders, transfers, or withdrawals."
        )
    except Exception as exc:
        await update.message.reply_text(
            f"⚠️ Balance unavailable: {type(exc).__name__}.\n"
            "No order was placed."
        )


async def riskcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /riskcheck <equity_usdt> [leverage]\n"
            "Example: /riskcheck 1000 20\n"
            "This is a dry risk check only; no order is sent."
        )
        return
    try:
        equity = float(context.args[0])
        leverage = int(context.args[1]) if len(context.args) > 1 else 20
        analysis = analyze(get_btcusdt_candles(interval="1h", limit=100))
        approved, message, result = evaluate_analysis(analysis, equity, leverage)
        if result is None:
            await update.message.reply_text(f"🛡️ RISK CHECK\n\n{message}")
            return
        details = (
            f"\nRisk amount: {result.risk_amount:.2f} USDT"
            f"\nPosition size: {result.position_size:.6f} BTC"
            f"\nReward/Risk: {result.reward_risk:.2f}"
            f"\nStop distance: {result.stop_distance_pct:.2f}%"
        )
        await update.message.reply_text(
            f"🛡️ RISK CHECK\n\n{message}{details}\n\n"
            "⚠️ DRY RUN ONLY — execution is disabled."
        )
    except (ValueError, TypeError):
        await update.message.reply_text("⚠️ Invalid equity/leverage. Example: /riskcheck 1000 20")


async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = analyze(get_btcusdt_candles(interval="1h", limit=100))
        if result.bias == "NO_TRADE":
            await update.message.reply_text(
                "🟡 BTC/USDT ANALYSIS\n\nDecision: NO TRADE\n"
                f"Reason: {result.reason}\nMode: READ-ONLY / DEMO"
            )
            return
        await update.message.reply_text(
            "📈 BTC/USDT ANALYSIS\n\n"
            f"Bias: {result.bias}\nScore: {result.score:.0f}/100\n"
            f"Entry reference: {result.entry}\nStop reference: {result.stop_loss}\n"
            f"Target reference: {result.take_profit}\nReason: {result.reason}\n\n"
            "⚠️ Analysis only. No order was sent."
        )
    except Exception as exc:
        await update.message.reply_text(f"⚠️ Analysis unavailable: {type(exc).__name__}.\nNo order was placed.")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = get_btcusdt_price()
        await update.message.reply_text(
            f"📊 BTC/USDT\n\nPrice: {result.price} USDT\n"
            "Source: Binance public market data\n"
            "Mode: READ-ONLY / DEMO"
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ BTC price is temporarily unavailable.\nNo order was placed."
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "price":
        try:
            result = get_btcusdt_price()
            await query.edit_message_text(
                f"📊 BTC/USDT\n\nPrice: {result.price} USDT\n"
                "Source: Binance public market data\n"
                "Mode: READ-ONLY / DEMO"
            )
        except Exception:
            await query.edit_message_text(
                "⚠️ BTC price is temporarily unavailable.\nNo order was placed."
            )
        return

    responses = {
        "settings": "⚙️ Settings\n\nLeverage hard limit: 20x\nRisk per trade: 0.5%\nMinimum RR: 1:2",
        "long": "🟢 LONG selected\n\nDEMO ONLY — no real order was sent.\nSignal validation + Risk Engine are required.",
        "short": "🔴 SHORT selected\n\nDEMO ONLY — no real order was sent.\nSignal validation + Risk Engine are required.",
        "trades": "📋 Open Trades\n\nNo real open trades.",
        "history": "📈 History\n\nNo trades yet.",
        "stop": "⛔ Trading stopped.\n\nReal execution is disabled.",
    }
    await query.edit_message_text(responses.get(query.data, "Unknown command."))


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("status", "Show bot status"),
        BotCommand("balance", "Show BTC/USDT balance (read-only)"),
        BotCommand("price", "Show BTC/USDT price"),
        BotCommand("analysis", "Show BTC/USDT analysis"),
        BotCommand("riskcheck", "Run a dry risk check"),
    ])


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing")
    start_health_server()
    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("analysis", analysis_command))
    app.add_handler(CommandHandler("riskcheck", riskcheck_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("BTC Telegram Bot V1 started in DEMO mode...")
    app.run_polling()


if __name__ == "__main__":
    main()
