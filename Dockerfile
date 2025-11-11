FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.8.9 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY omero_prometheus_tools/ ./omero-prometheus-tools/

RUN uv venv --python 3.12 && uv sync
RUN useradd -m -u 1000 omero \
    && chown -R omero:omero /app

USER omero
EXPOSE 9449
WORKDIR /data

ENTRYPOINT ["uv", "run", "python", "-m", "omero-prometheus-tools"]
