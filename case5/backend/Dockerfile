FROM python:3.9-slim

WORKDIR /app

# Install dependencies first (caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY app.py .
COPY kodewilayah.csv .

EXPOSE 5000

CMD ["python", "app.py"]
