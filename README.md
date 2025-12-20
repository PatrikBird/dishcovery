# Dishcovery 

A blazing-fast recipe search service built with **FastAPI**, **Elasticsearch**, and **Kubernetes**.

## Features

- **Lightning-fast search** across 62,000+ recipes (10-50ms response times)
- **Multi-field search** across titles, descriptions, ingredients, and directions
- **Advanced filtering** by cuisine, dietary preferences, prep time, and healthiness score
- **Auto-generated API docs** at `/docs`

## Quick Start

### 1. Start Infrastructure Services
```bash
docker-compose up -d
```

### 2. Run FastAPI Locally (Development)
```bash
cd api
pip install uv
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Data will be automatically loaded from [recipes.json](data/recipes.json) into Elasticsearch on first run.

> **Note**: For development, FastAPI runs locally while Elasticsearch runs in Docker for optimal development experience.

### 3. Search Recipes
```bash
# Basic search
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "pasta", "size": 5}'

# Filtered search
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "", "cuisines": ["korean"], "is_vegan": true, "max_prep_time": 30}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | HTML welcome page (Jinja2 + HTMX) |
| `/health` | GET | Health check (API + Elasticsearch status) |
| `/search` | POST | Search recipes with query parameters |
| `/bulk-load` | POST | Load all recipes into Elasticsearch |
| `/docs` | GET | Interactive API documentation |

## Search Examples

### Basic Text Search
```bash
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "chocolate", "size": 3}'
```

### Cuisine & Dietary Filters
```bash
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "", "cuisines": ["italian"], "is_vegan": true, "size": 5}'
```

### Time-based Filtering
```bash
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "breakfast", "max_prep_time": 15, "size": 10}'
```

### Complex Search
```bash
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "healthy chicken", "cuisines": ["asian"], "max_prep_time": 30, "size": 5}'
```

## Response Format

See [example_output.json](data/example_output.json) for a sample search response.

## Roadmap

- [x] Advanced POST search endpoint with JSON body
- [x] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Frontend
- [?] Recipe recommendation engine
- [?] Elasticsearch cluster scaling
