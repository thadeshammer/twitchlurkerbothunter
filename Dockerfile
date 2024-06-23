FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

RUN apt-get update && apt-get install -y default-mysql-client

COPY . .

# Create log directory
RUN mkdir -p /logs

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV LOG_CFG="logging_config.yaml"
ENV DATABASE_URL="mysql+pymysql://user:password@db/mydatabase"
ENV SECRETS_DIR="./secrets/tokens.yaml"

# Expose the port
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
