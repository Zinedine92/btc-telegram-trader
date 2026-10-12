"""Passenger WSGI entrypoint and single-instance Telegram bot supervisor.

The Telegram bot only exposes analysis and read-only account inspection. This
module never places exchange orders. A file lock prevents duplicate pollers when
Passenger loads multiple workers.
"""
import asyncio
import fcntl
import threading
import time

_LOCK_PATH = "/tmp/btc-telegram-trader-isaamojw.lock"


def _run_telegram_bot():
    lock_file = open(_LOCK_PATH, "a")
    try:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Another Passenger worker already owns the Telegram polling loop.
            return

        while True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from bot import main
                print("Telegram supervisor: starting bot (read-only/demo mode).")
                main(embedded=True)
                print("Telegram supervisor: polling returned; restarting.")
            except Exception as exc:
                # Do not print exception text because it may include URLs or data.
                print("Telegram supervisor: startup/runtime failure:", type(exc).__name__)
            finally:
                try:
                    if not loop.is_closed():
                        loop.close()
                except Exception:
                    pass
                asyncio.set_event_loop(None)
            time.sleep(10)
    finally:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()


_supervisor = threading.Thread(
    target=_run_telegram_bot,
    name="telegram-polling-supervisor",
    daemon=True,
)
_supervisor.start()


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path not in ("/", "/health"):
        body = b"Not Found"
        status = "404 Not Found"
    else:
        state = b"supervisor-started" if _supervisor.is_alive() else b"supervisor-not-running"
        body = b"WSGI OK; Telegram supervisor " + state + b". Check application logs for bot status."
        status = "200 OK" if _supervisor.is_alive() else "503 Service Unavailable"

    start_response(
        status,
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]
