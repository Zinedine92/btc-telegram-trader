"""Passenger WSGI health endpoint and Telegram bot supervisor.

Exposes a truthful health status for the background bot thread. Secret values
are never logged or returned. Trading remains analysis/read-only only.
"""
import asyncio
import fcntl
import os
import threading
import time
import traceback

_LOCK_PATH = "/tmp/btc-telegram-trader-isaamojw.lock"
_state_lock = threading.Lock()
_state = {"status": "starting", "error": None, "updated": time.time()}


def _set_state(status, error=None):
    with _state_lock:
        _state.update(status=status, error=error, updated=time.time())


def _run_telegram_bot():
    try:
        lock_file = open(_LOCK_PATH, "a")
    except Exception as exc:
        _set_state("error", type(exc).__name__)
        print("Telegram supervisor: cannot open lock:", type(exc).__name__, flush=True)
        return

    with lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _set_state("duplicate-worker", None)
            print("Telegram supervisor: another worker owns the bot lock.", flush=True)
            return

        while True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if not os.getenv("BOT_TOKEN"):
                    raise RuntimeError("BOT_TOKEN_MISSING")
                from bot import main
                _set_state("starting-polling")
                print("Telegram supervisor: starting polling (read-only/demo).", flush=True)
                main(embedded=True)
                _set_state("polling-returned")
                print("Telegram supervisor: polling returned; retrying.", flush=True)
            except Exception as exc:
                error_type = "BOT_TOKEN_MISSING" if str(exc) == "BOT_TOKEN_MISSING" else type(exc).__name__
                _set_state("error", error_type)
                print("Telegram supervisor: startup/runtime failure:", error_type, flush=True)
                traceback.print_exc()
            finally:
                try:
                    if not loop.is_closed():
                        loop.close()
                except Exception:
                    pass
                asyncio.set_event_loop(None)
            time.sleep(10)


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
        with _state_lock:
            current = dict(_state)
        error = current["error"] or "none"
        body = (
            "WSGI OK; supervisor_thread="
            + ("alive" if _supervisor.is_alive() else "stopped")
            + "; bot_status=" + str(current["status"])
            + "; error_type=" + str(error)
        ).encode("utf-8")
        status = "200 OK" if _supervisor.is_alive() else "503 Service Unavailable"

    start_response(
        status,
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ],
    )
    return [body]
