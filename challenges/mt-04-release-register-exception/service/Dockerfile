FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
# Keep Python from writing bytecode and send logs directly to the container output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && groupadd --system --gid 10001 mt04 \
    && useradd --system --uid 10001 --gid mt04 --home-dir /app --no-create-home mt04
COPY app.py db.py seed.py /app/
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY data/seed.sqlite /app/data/seed.sqlite
# Allow the service user to read the application while keeping the seed database read-only.
RUN chown -R 10001:10001 /app && chmod 0444 /app/data/seed.sqlite
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
