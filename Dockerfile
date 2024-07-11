FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y default-mysql-client

COPY . .

# Copy SSL certificates
COPY secrets/cert.pem /secrets/cert.pem
COPY secrets/key.pem /secrets/key.pem

# Create log directory
RUN mkdir -p /logs

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV LOG_CFG="logging_config.yaml"
ENV DATABASE_URL="mysql+pymysql://user:password@db/mydatabase"
ENV SECRETS_DIR="./secrets/tokens.yaml"

# Expose the port
EXPOSE 443

CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "443", "--ssl-certfile", "/secrets/cert.pem", "--ssl-keyfile", "/secrets/key.pem"]
