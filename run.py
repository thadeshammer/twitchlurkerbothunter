import logging.config
import os
import ssl

from app import create_app
from app.config import Config
from app.util import setup_logging

CERT_FILE_PATH = "/secrets/cert.pem"
KEY_FILE_PATH = "/secrets/key.pem"

CERT_PASSKEY = str(os.getenv("CERT_PASSKEY"))
if not CERT_PASSKEY:
    raise EnvironmentError("CERT_PASSKEY environment variable not set")

# Logger setup outside of create_app
setup_logging(Config.LOGGING_CONFIG_FILE)
logging.getLogger("asyncio").setLevel(
    logging.WARNING
)  #  "Using selector: EpollSelector" spam
logger = logging.getLogger("app")
logger.info("Logger is ready.")

app = create_app()


@app.teardown_appcontext
def shutdown_event(exception=None):
    logger.info("Server is shutting down...")
    if exception is not None:
        logger.error(f"Shutdown error: {exception}")


if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=CERT_FILE_PATH,
        keyfile=KEY_FILE_PATH,
        password=CERT_PASSKEY,
    )

    app.run(debug=True, ssl_context=context, port=443)
