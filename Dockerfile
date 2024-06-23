FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

RUN apt-get update && apt-get install -y default-mysql-client

COPY . .

# Copy SSL certificates
COPY secrets/cert.pem /secrets/cert.pem
COPY secrets/key.pem /secrets/key.pem

# Create log directory
RUN mkdir -p /logs

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV LOG_CFG="logging_config.yaml"
ENV DATABASE_URL="mysql+pymysql://user:password@db/mydatabase"
ENV SECRETS_DIR="./secrets/tokens.yaml"

# Expose the port
EXPOSE 443

CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:443", "--certfile=/secrets/cert.pem", "--keyfile=/secrets/key.pem", "run:app"]
