FROM python:3.12-slim

WORKDIR /app

# Git is used by the History tab to read commit log of the OKR data
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Default location for OKR data when mounted as a volume
ENV OKR_DATA_DIR=/data
ENV PORT=5050

EXPOSE 5050

# Use gunicorn in production; debug Flask server is for dev only
RUN pip install --no-cache-dir gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 60 app:app"]
