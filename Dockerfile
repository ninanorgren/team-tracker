FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

ENV FLASK_APP=run.py

CMD ["gunicorn", "--bind", "0.0.0.0:7000", "--workers", "3", "run:app"]
