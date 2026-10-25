"""Telegram interface for the BTC/USDT trading bot.

Demo/analysis-only mode. No exchange orders are placed.
"""

import asyncio
import functools
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError

from dotenv import load_dotenv
from telegram import BotCommand, BotCommandScopeAllPrivateChats, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from binance_balance import get_btc_usdt_balances
from binance_readonly_client import describe_http_error
import access
import dashboard
import market_data
from market_data import get_btcusdt_price, get_btcusdt_candles
from strategy import analyze
from risk_gate import evaluate_analysis


# Load environment variables from .env file (if it exists)
load_dotenv()


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
    if port <= 0:
        print("Health server disabled because PORT is not positive.")
        return
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    except OSError as exc:
        print(f"Health server failed to bind to port {port}: {exc}")
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Health server listening on 0.0.0.0:{port}")


def owner_only(handler):
    """Run the handler only for Telegram user IDs listed in ALLOWED_USER_IDS."""
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not access.is_authorized(user.id if user else None):
            if update.callback_query:
                await update.callback_query.answer("Unauthorized", show_alert=True)
            elif update.message:
                await update.message.reply_text(
                    "⛔ Unauthorized. This bot is private.\n"
                    "Send /myid to get your Telegram ID, then set ALLOWED_USER_IDS on the server."
                )
            return
        await handler(update, context)
    return wrapper


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reveals only the sender's own numeric Telegram ID (needed to set the allowlist)."""
    user = update.effective_user
    await update.message.reply_text(f"Your Telegram ID: {user.id if user else 'unknown'}")


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


async def diag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Report only whether runtime variables exist; never reveal their values."""
    key_set = bool(os.getenv("BINANCE_API_KEY"))
    secret_set = bool(os.getenv("BINANCE_API_SECRET"))
    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()
    live_opt_in = os.getenv("ENABLE_LIVE_TRADING", "").strip().upper() == "YES"
    await update.message.reply_text(
        "🔎 SAFE RUNTIME DIAGNOSTIC\n\n"
        f"BOT_TOKEN: {'SET' if os.getenv('BOT_TOKEN') else 'MISSING'}\n"
        f"BINANCE_API_KEY: {'SET' if key_set else 'MISSING'}\n"
        f"BINANCE_API_SECRET: {'SET' if secret_set else 'MISSING'}\n"
        f"BINANCE_MODE: {mode}\n"
        f"Live trading opt-in: {'YES' if live_opt_in else 'NO'}\n\n"
        "Only variable presence is checked; secret values are never shown. "
        "No Binance request or order is made."
    )


def panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Portfolio", callback_data="panel_portfolio"),
         InlineKeyboardButton("📋 Open orders", callback_data="panel_orders")],
        [InlineKeyboardButton("📈 Analysis", callback_data="panel_analysis"),
         InlineKeyboardButton("📊 Price", callback_data="panel_price")],
    ])


def _panel_error_text(exc):
    """Secret-free explanation of why a Binance read failed."""
    if isinstance(exc, HTTPError):
        detail = describe_http_error(exc)
        hint = ("\nBinance blocks this server's region. Run the bot from an allowed country."
                if exc.code == 451 else "")
        return f"⚠️ Binance returned {detail}.{hint}\nNo order was placed."
    if isinstance(exc, RuntimeError):
        return "⚠️ Binance configuration/credentials problem. Check /diag.\nNo order was placed."
    return f"⚠️ Unavailable: {type(exc).__name__}.\nNo order was placed."


async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎛 CONTROL PANEL\n\nRead-only view of your Binance Spot account and the strategy.\n"
        "No trading from this bot.",
        reply_markup=panel_keyboard(),
    )


async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    try:
        if action == "panel_portfolio":
            rows, total = await asyncio.to_thread(dashboard.fetch_portfolio)
            text = dashboard.format_portfolio(rows, total)
        elif action == "panel_orders":
            orders = await asyncio.to_thread(dashboard.fetch_open_orders)
            text = dashboard.format_open_orders(orders)
        elif action == "panel_price":
            result = await asyncio.to_thread(get_btcusdt_price)
            text = (f"📊 BTC/USDT\n\nPrice: {result.price} USDT\n"
                    f"Source: {market_data.LAST_SOURCE} public market data")
        elif action == "panel_analysis":
            candles = await asyncio.to_thread(get_btcusdt_candles, "1h", 200)
            r = analyze(candles)
            text = (f"🟡 ANALYSIS: NO TRADE\n{r.reason}" if r.bias == "NO_TRADE" else
                    f"📈 ANALYSIS: {r.bias} (score {r.score:.0f}/100)\nEntry {r.entry}  Stop {r.stop_loss}  Target {r.take_profit}\n"
                    "⚠️ Analysis only.")
        else:
            text = "Unknown panel action."
    except Exception as exc:
        print("Panel action failed:", action, type(exc).__name__)
        text = _panel_error_text(exc)
    await query.edit_message_text(text, reply_markup=panel_keyboard())


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
    except RuntimeError as exc:
        # Report only safe, known configuration causes. Never expose credentials.
        message = str(exc)
        if "credentials" in message.lower() or "api key" in message.lower():
            detail = (
                "Binance API credentials are unavailable to the running process. "
                "Check the application's environment variables and restart the app."
            )
        elif "TESTNET" in message or "LIVE mode is blocked" in message:
            detail = (
                "Binance mode configuration blocked the request. Keep TESTNET enabled "
                "while diagnosing; real trading remains disabled."
            )
        else:
            detail = "A runtime configuration check failed. Check the hosting error log."
        await update.message.reply_text(
            f"⚠️ Balance unavailable: {detail}\nNo order was placed."
        )
    except HTTPError as exc:
        # Binance's HTTP status and error code/message contain no credentials.
        detail = describe_http_error(exc)
        print("Balance check failed:", detail)
        await update.message.reply_text(
            f"⚠️ Balance unavailable: Binance returned {detail}.\n"
            "No order was placed."
        )
    except Exception as exc:
        # Log only the exception type, not its message, URL, headers, or secrets.
        print("Balance check failed; exception type:", type(exc).__name__)
        await update.message.reply_text(
            f"⚠️ Balance unavailable: {type(exc).__name__}. "
            "Check the hosting application error log for details.\n"
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
        analysis = analyze(get_btcusdt_candles(interval="1h", limit=200))
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
        result = analyze(get_btcusdt_candles(interval="1h", limit=200))
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
            f"Source: {market_data.LAST_SOURCE} public market data\n"
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
                f"Source: {market_data.LAST_SOURCE} public market data\n"
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
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("myid", "Show your Telegram ID"),
        BotCommand("status", "Show bot status"),
        BotCommand("panel", "Open the read-only control panel"),
        BotCommand("balance", "Show BTC/USDT balance (read-only)"),
        BotCommand("diag", "Check safe runtime configuration"),
        BotCommand("price", "Show BTC/USDT price"),
        BotCommand("analysis", "Show BTC/USDT analysis"),
        BotCommand("riskcheck", "Run a dry risk check"),
    ]
    await application.bot.set_my_commands(commands)
    await application.bot.set_my_commands(
        commands,
        scope=BotCommandScopeAllPrivateChats(),
    )


def main(*, embedded=False):
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Set it in your environment or .env file before runtime.")
    # Passenger already serves the WSGI health endpoint; avoid binding a second port.
    if not embedded:
        start_health_server()
    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", owner_only(start)))
    app.add_handler(CommandHandler("status", owner_only(status)))
    app.add_handler(CommandHandler("balance", owner_only(balance_command)))
    app.add_handler(CommandHandler("diag", owner_only(diag_command)))
    app.add_handler(CommandHandler("price", owner_only(price_command)))
    app.add_handler(CommandHandler("analysis", owner_only(analysis_command)))
    app.add_handler(CommandHandler("riskcheck", owner_only(riskcheck_command)))
    app.add_handler(CommandHandler("panel", owner_only(panel_command)))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CallbackQueryHandler(owner_only(panel_callback), pattern="^panel_"))
    app.add_handler(CallbackQueryHandler(owner_only(button_handler)))
    print("BTC Telegram Bot V1 started in DEMO mode...")
    # Passenger starts this from a background thread, where signal handlers are unavailable.
    if embedded:
        app.run_polling(drop_pending_updates=True, stop_signals=None)
    else:
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
