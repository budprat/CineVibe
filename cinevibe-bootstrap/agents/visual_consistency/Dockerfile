FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py .
COPY a2a_server.py .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the A2A server
CMD ["python", "a2a_server.py"]