import os
import ssl

from app import create_app

CERT_FILE_PATH = "/secrets/cert.pem"
KEY_FILE_PATH = "/secrets/key.pem"

CERT_PASSKEY = str(os.getenv("CERT_PASSKEY"))
if not CERT_PASSKEY:
    raise EnvironmentError("CERT_PASSKEY environment variable not set")

app = create_app()


if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=CERT_FILE_PATH,
        keyfile=KEY_FILE_PATH,
        password=CERT_PASSKEY,
    )

    app.run(debug=True, ssl_context=context, port=443)
