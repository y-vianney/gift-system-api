FROM python:3.11-slim
LABEL authors="Vy.03"

# Sécurité de base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY . .

# Port FastAPI
EXPOSE 8000

# Lancement prod
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]