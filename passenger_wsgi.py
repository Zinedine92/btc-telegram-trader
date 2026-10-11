"""WSGI endpoint plus a single-instance Telegram polling supervisor for cPanel Passenger.

Passenger supplies this application's configured environment variables. A process
lock prevents multiple Passenger workers from polling Telegram with the same token.
The Telegram bot remains demo/read-only: it does not place orders.
"""
import fcntl
import os
import threading
import time

_LOCK_PATH = "/tmp/btc-telegram-trader-polling.lock"


def _telegram_supervisor():
    while True:
        lock_file = None
        try:
            lock_file = open(_LOCK_PATH, "a", encoding="utf-8")
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_file.close()
                lock_file = None
                time.sleep(15)
                continue

            # Keep the lock held for the entire polling lifetime.
            print("Telegram supervisor acquired single-instance lock.")
            from bot import main
            main(embedded=True)
            print("Telegram bot polling returned; supervisor will retry.")
        except Exception as exc:
            # Do not log exception text: it could contain request details.
            print("Telegram bot startup/runtime failed: " + type(exc).__name__)
        finally:
            if lock_file is not None:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                except Exception:
                    pass
        time.sleep(15)


_supervisor = threading.Thread(
    target=_telegram_supervisor,
    name="telegram-bot-supervisor",
    daemon=True,
)
_supervisor.start()


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path not in ("/", "/health"):
        body = b"Not Found"
        status = "404 Not Found"
    else:
        body = b"WSGI OK. Telegram polling supervisor is enabled; check application logs for bot status."
        status = "200 OK"

    start_response(
        status,
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]
