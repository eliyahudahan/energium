FROM python:3.12-slim

# Install system dependencies required by LightGBM (OpenMP)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what the API needs
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the specific API files and the model
COPY api/main.py ./api/main.py
COPY models/lgbm_model.pkl ./models/lgbm_model.pkl

# Expose the port and run
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]