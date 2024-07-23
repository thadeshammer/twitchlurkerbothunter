FROM python:3.11-slim

WORKDIR /server

# run pip install first + cache it
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# slower but more space efficient
# RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y default-mysql-client

# Copy SSL certificates and client id & secret
COPY secrets/cert.pem /secrets/cert.pem
COPY secrets/key.pem /secrets/key.pem
COPY secrets/tokens.yaml /secrets/tokens.yaml

# Copy application code
COPY . .

# Create log directory
RUN mkdir -p /logs

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV ENVIRONMENT="container"
ENV LOG_CFG="logging_config.yaml"
ENV SECRETS_DIR="/secrets/tokens.yaml"

ENV DBNAME="lurkerbothunterdb"
ENV DB_SERVICE_NAME="db"
ENV DB_PORT="3306"

ENV REDIS_HOST="localhost"
ENV REDIS_PORT="6379"
ENV REDIS_DB_INDEX="0"

COPY ./secrets/.mysql_root_password.txt /run/secrets/mysql_root_password
COPY ./secrets/.mysql_user_password.txt /run/secrets/mysql_user_password
COPY ./secrets/.testdb_user_password.txt /run/secrets/testdb_user_password
RUN chmod 400 /run/secrets/mysql_root_password /run/secrets/mysql_user_password /run/secrets/testdb_user_password

EXPOSE 443

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "/secrets/key.pem", "--ssl-certfile", "/secrets/cert.pem"]