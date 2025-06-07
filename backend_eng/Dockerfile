FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 確保安裝 gunicorn + uvicorn worker
RUN pip install gunicorn "uvicorn[standard]"
RUN pip install mysql-connector-python

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p app/static/uploads/pdfs app/static/uploads/photos

# Expose port
EXPOSE 8000

# # Command to run the application
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 使用 Gunicorn 啟動 FastAPI
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4"]