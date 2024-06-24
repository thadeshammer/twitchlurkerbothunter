# gunicorn_config.py
# Leaving this here as a breadcrumb incase we wind up with more complex shutdown requirements.
import signal

from gunicorn.arbiter import Arbiter


def on_exit(server: Arbiter):  # type: ignore
    # Your shutdown logic here
    print("Server is shutting down...")


def when_ready(server: Arbiter):
    signal.signal(signal.SIGTERM, lambda *args: on_exit(server))
    signal.signal(signal.SIGINT, lambda *args: on_exit(server))
