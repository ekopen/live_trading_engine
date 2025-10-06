FROM python:3.10-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy shared requirements from the common folder
COPY ./common/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy this service’s source code
COPY ./market_data_stream ./

# Ensure logs directory exists
RUN mkdir -p /app/logs

CMD ["python", "src/main.py"]
