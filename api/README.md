# Dishcovery API Development

## Setup

1. **Start infrastructure services:**
   ```bash
   # From project root
   docker-compose down  # Clean up any old containers
   docker-compose up -d
   ```

2. **Install Python dependencies:**
   ```bash
   # From api/ directory
   cd api
   pip install uv
   uv sync
   ```

3. **Run FastAPI locally:**
   ```bash
   # From api/ directory
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Troubleshooting

- **Port 8000 in use**: Stop any orphaned containers with `docker ps -a` and `docker stop/rm`
- **uvicorn not found**: Run `uv sync --reinstall` to reinstall dependencies

## Services

- **FastAPI**: http://localhost:8000 (runs locally)
- **Elasticsearch**: http://localhost:9200
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## Development

The FastAPI app runs locally with auto-reload, connecting to dockerized Elasticsearch. Code changes are reflected immediately without container rebuilds.