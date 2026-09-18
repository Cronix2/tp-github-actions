# Stage 1 : installation des dépendances
FROM python:3.12 AS builder

WORKDIR /app

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir --timeout 15 --retries 2 -r requirements.txt

# Stage 2 : image finale légère
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY app.py .

RUN useradd --create-home appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]