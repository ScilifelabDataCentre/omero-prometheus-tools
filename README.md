[![OMERO](https://github.com/ome/omero-prometheus-tools/workflows/OMERO/badge.svg)](https://github.com/ome/omero-prometheus-tools/actions)

[![PyPI version](https://badge.fury.io/py/omero-prometheus-tools.svg)](https://badge.fury.io/py/omero-prometheus-tools)

# Tools for monitoring OMERO with Prometheus

This repository is under development.
Breaking changes may be made without warning.

## Installation

The easiest way to run is using UV:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

Build the package:

```bash
uv build
```

Install the package in a fresh virtual environment with Zeroc Ice Glencoe pre-compiled package:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install "https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/releases/download/20240202/zeroc_ice-3.6.5-cp312-cp312-manylinux_2_28_x86_64.whl"
uv pip install dist/omero_prometheus_tools-0.3.0-py3-none-any.whl
```

## Running

Then run the tool:

```bash
uv run python -m omero_prometheus_tools \
    -s omero.scilifelab.se -u <user> -w <password> \
    -c omero_prometheus_tools/etc/prometheus-omero-counts.yaml
```

Metrics will be published on http://localhost:9449
