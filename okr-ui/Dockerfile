FROM python:3.12-slim

WORKDIR /app

# git is used by the History tab to read the OKR data dir's commit log
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repo root (Render's default), so reference
# files via the okr-ui/ prefix.
COPY okr-ui/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY okr-ui/app.py okr-ui/parser.py ./
COPY okr-ui/templates ./templates

# Seed /data with the demo OKR markdown files so a fresh deploy works
# without first having to mount and populate a persistent volume.
# Mount a real volume at /data later to replace these with your team's
# actual OKRs and keep edits across container restarts.
RUN mkdir -p /data
COPY *.md /data/

ENV OKR_DATA_DIR=/data

# Render injects PORT at runtime; fall back to 5050 for local docker run.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5050} --workers 2 --timeout 60 app:app"]
