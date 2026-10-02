FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core fonts-hosny-amiri \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server.py ./
COPY dist ./dist
RUN mkdir -p /app/data && useradd --system --uid 10001 --home /app jisr && chown -R jisr:jisr /app/data
USER jisr
ENV JISR_HOST=0.0.0.0 JISR_PORT=8766 JISR_DATA_DIR=/app/data PYTHONUNBUFFERED=1
EXPOSE 8766
VOLUME ["/app/data"]
CMD ["python", "server.py"]
