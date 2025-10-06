FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Install required OS packages
RUN apt-get update && apt-get install -y gcc

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Run the pipeline (adjust if you use uvicorn directly)
CMD ["python", "main.py"]