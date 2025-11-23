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
- [Python 3.11+](https://www.python.org/downloads/)
- [UV package manager](https://github.com/astral-sh/uv)
- [Docker Compose](https://github.com/docker/compose)

### 1. Start App with Docker Compose
```bash
docker-compose up --build -d
```

Data will be automatically loaded from [recipes.json](data/recipes.json) into Elasticsearch on first run.

### 2. Search Recipes
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
| `/` | GET | Welcome message |
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

```json
{
"total": 3662,
"recipes": [
  {
    "recipe_title": "Air Fryer Potato Slices with Dipping Sauce",
    "description": "These air fryer potato slices, served with a beer ketchup dipping sauce [...]",
    "cuisine_list": [
        "american",
        "american_region",
        "asian",
        "..."
    ],
    "difficulty": "hard",
    "est_prep_time_min": 23,
    "est_cook_time_min": 74,
    "is_vegan": true,
    "is_vegetarian": true,
    "is_gluten_free": true,
    "healthiness_score": 80,
    "ingredients_raw": [
        "3/4 cup ketchup",
        "1/2 cup beer",
        "..."
    ],
    "directions_raw": [
        "Combine ketchup, beer [...]"
    ]
  }
],
"took_ms": 20,
"aggregations": null
}```

## Roadmap

- [x] Advanced POST search endpoint with JSON body
- [x] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Frontend
- [ ] Recipe recommendation engine
- [ ] Elasticsearch cluster scaling
