FROM python:3.11-slim
LABEL authors="Vy.03"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000

# Production launch
CMD ["uvicorn", "gift_system.api:app", "--host", "0.0.0.0", "--port", "8000"]