# Use an official lightweight Python image
FROM python:3.13.5-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI service code
COPY app.py .

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the service with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
