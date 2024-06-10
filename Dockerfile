FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y default-mysql-client

COPY . .

# Create log directory
RUN mkdir -p /logs

# Set environment variables
ENV LOG_CFG=logging_config.yaml

# Expose the port
EXPOSE 8000

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
