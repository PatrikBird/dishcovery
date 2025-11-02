# Dishcovery 

A blazing-fast recipe search service built with **FastAPI**, **Elasticsearch**, and **Kubernetes**.

## Features

- **Lightning-fast search** across 62,000+ recipes (10-50ms response times)
- **Multi-field search** across titles, descriptions, ingredients, and directions
- **Advanced filtering** by cuisine, dietary preferences, prep time, and healthiness score
- **Production-ready** with Kubernetes deployment and health checks
- **Auto-generated API docs** at `/docs`

## Quick Start

### Prerequisites
- Python 3.11+
- Minikube
- UV package manager

### 1. Start Minikube & Deploy Elasticsearch
```bash
minikube start
kubectl apply -f k8s/elasticsearch/
kubectl port-forward elasticsearch-0 9200:9200
```

### 2. Start FastAPI Application
```bash
cd app
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Load Recipe Data
```bash
curl -X POST "localhost:8000/bulk-load"
```

### 4. Search Recipes
```bash
# Basic search
curl "localhost:8000/search?q=pasta&size=5"

# Filtered search  
curl "localhost:8000/search?cuisine=korean&is_vegan=true&max_prep_time=30"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check (API + Elasticsearch status) |
| `/search` | GET | Search recipes with query parameters |
| `/bulk-load` | POST | Load all recipes into Elasticsearch |
| `/docs` | GET | Interactive API documentation |

## Search Examples

### Basic Text Search
```bash
curl "localhost:8000/search?q=chocolate&size=3"
```

### Cuisine & Dietary Filters
```bash
curl "localhost:8000/search?cuisine=italian&is_vegan=true&size=5"
```

### Time-based Filtering
```bash
curl "localhost:8000/search?q=breakfast&max_prep_time=15&size=10"
```

### Complex Search
```bash
curl "localhost:8000/search?q=healthy+chicken&cuisine=asian&max_prep_time=30&size=5"
```

## Response Format

```json
{
  "total": 3033,
  "recipes": [
    {
      "recipe_title": "Quick Vegan Pasta",
      "description": "Simple 15-minute vegan pasta dish",
      "cuisine_list": ["Italian"],
      "est_prep_time_min": 5,
      "est_cook_time_min": 10,
      "is_vegan": true,
      "healthiness_score": 75,
      "ingredients_raw": ["1 cup pasta", "2 tbsp olive oil"],
      "directions_raw": ["Boil pasta", "Add olive oil"]
    }
  ],
  "took_ms": 17
}
```

## Roadmap

- [ ] Advanced POST search endpoint with JSON body
- [ ] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Recipe recommendation engine
- [ ] Elasticsearch cluster scaling
