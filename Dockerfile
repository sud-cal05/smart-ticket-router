FROM python:3.11-slim

# Non-root user (M4E3)
RUN useradd --create-home appuser
WORKDIR /app

# Dependency layer first — cached across rebuilds unless requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then source
COPY . .

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')" || exit 1
# API key is passed at run time via --env-file, never baked in
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]