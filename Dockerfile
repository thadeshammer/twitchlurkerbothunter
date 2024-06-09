FROM python:3.11-slim

WORKDIR /server

# src lives in /server in local and container
COPY . /server

# install requirements
RUN pip install --no-cache-dir -r requirements.txt

# TODO 443 / tokens / oauth
EXPOSE 80

# invoke uvicorn with hot-reload
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--reload-dir", "/server", "--log-config", "./logging_config.yml"]