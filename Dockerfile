FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core fonts-hosny-amiri \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server.py ./
COPY subtitle_png.py ./
COPY pipeline_quality.py ./
COPY docker-entrypoint.py ./
COPY dist ./dist
RUN mkdir -p /app/data && useradd --system --uid 10001 --home /app jisr && chown -R jisr:jisr /app/data
# Initialize a newly mounted volume, then run the application as jisr.
ENV JISR_HOST=0.0.0.0 JISR_DATA_DIR=/app/data PYTHONUNBUFFERED=1
EXPOSE 8766
VOLUME ["/app/data"]
ENTRYPOINT ["python", "docker-entrypoint.py"]
CMD ["python", "server.py"]
