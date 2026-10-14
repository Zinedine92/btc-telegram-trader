# btc-telegram-trader

Python Telegram bot for read-only BTC/USDT market analysis and demo risk checks.
No exchange orders are placed.

## Runtime
- Python 3.11+ (the code uses `X | None` type syntax, which needs Python 3.10+)
- Starts from `python bot.py`

## Environment
Copy `env.example` to `.env` and set the values before running the bot.
`BOT_TOKEN` is required. Binance keys are only needed for `/balance`.

## Namecheap/cPanel notes
- `passenger_wsgi.py` starts the Telegram polling loop in a background thread and
  serves a `/health` endpoint. In "Setup Python App", choose Python 3.11 or newer,
  set the environment variables there, install `requirements.txt`, then restart the app.
- Shared hosting may not keep a background Python process alive after restarts.
  Alternatively run the bot with `nohup python bot.py` in a cPanel terminal.

## Startup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
python bot.py
```

## Tests
```bash
python -m unittest discover -s tests -v
```
