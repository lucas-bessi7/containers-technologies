FROM python:3.10-alpine3.21
LABEL maintainer="Lucas Bessi"
WORKDIR /app
COPY requirements.txt .
RUN apk add --no-cache curl && pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
