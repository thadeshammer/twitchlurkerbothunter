FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y default-mysql-client

COPY . .

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
