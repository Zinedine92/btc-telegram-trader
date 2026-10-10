"""Minimal WSGI health endpoint for cPanel Passenger.

The Telegram bot is a separate long-running polling process. Do not start
bot.py from this module: Passenger can import the WSGI module multiple times.
"""


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    if path not in ("/", "/health"):
        body = b"Not Found"
        status = "404 Not Found"
    else:
        body = b"WSGI OK. Telegram bot runs separately."
        status = "200 OK"

    start_response(
        status,
        [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]
