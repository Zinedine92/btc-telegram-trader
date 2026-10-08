# btc-telegram-trader

Python Telegram bot for read-only BTC/USDT market analysis and demo risk checks.

## Runtime
- Python 3.11+
- Starts from `python bot.py`

## Environment
Copy `env.example` to `.env` and set the values before running the bot.

## Namecheap/cPanel notes
- This bot is a long-running polling process, not a static site or WSGI app.
- Shared hosting often does not keep a background Python process alive after restarts.
- Use a persistent process manager or run the bot via `nohup python bot.py` in a cPanel terminal.

## Startup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
python bot.py
```
