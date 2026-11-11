FROM python:3.12-slim

# Install system dependencies required by LightGBM (OpenMP)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the clean API requirements
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code and the model
COPY api/ ./api/
COPY models/ ./models/

# Expose the port and run
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]