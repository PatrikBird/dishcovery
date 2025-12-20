# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

## Project Information

### Repository Overview
**Dishcovery** is a blazing-fast recipe search service built with FastAPI, Elasticsearch, and Kubernetes. The project contains 62,000+ recipes with 10-50ms response times.

### Architecture & Technology Stack

#### Core Components
- **Backend API**: FastAPI (Python 3.14) with async/await patterns
- **Search Engine**: Elasticsearch 8.11.0 with custom analyzers and mappings
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Containerization**: Docker & Docker Compose for local dev, Kubernetes for production
- **Package Management**: UV (modern Python package manager)

#### Dependencies (api/pyproject.toml)
- `fastapi>=0.120.4` - Web framework
- `elasticsearch>=8.0.0,<9.0.0` - Search client
- `prometheus-client>=0.23.1` - Metrics collection
- `pydantic>=2.12.3` - Data validation
- `uvicorn[standard]>=0.38.0` - ASGI server
- Dev tools: `ruff>=0.14.4` for linting

#### Key Features
- Multi-field search across titles, descriptions, ingredients, directions
- Advanced filtering: cuisine, dietary preferences, prep time, healthiness score
- Real-time aggregations for faceted search
- Prometheus metrics with custom counters and histograms
- Auto-generated API docs at `/docs`

### Development Workflows

#### Quick Start
```bash
# Start full stack
docker-compose up --build -d

# Test dataset validation
python test_dataset.py [path/to/recipes.json]
```

#### API Endpoints
- `GET /` - Welcome message
- `GET /health` - Health check (API + Elasticsearch status)
- `POST /search` - Search recipes with JSON query parameters
- `POST /bulk-load` - Load all recipes into Elasticsearch
- `GET /docs` - Interactive API documentation
- `GET /metrics` - Prometheus metrics

#### Search Examples
```bash
# Basic search
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "pasta", "size": 5}'

# Filtered search with aggregations
curl -X POST localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "", "cuisines": ["korean"], "is_vegan": true, "max_prep_time": 30, "include_aggregations": true}'
```

### File Structure
```
dishcovery/
├── api/                          # FastAPI backend
│   ├── main.py                   # Main application with endpoints
│   ├── models.py                 # Pydantic models for requests/responses
│   ├── elasticsearch_client.py   # Async ES client wrapper
│   ├── config.py                 # Configuration settings
│   ├── pyproject.toml           # Python dependencies
│   ├── uv.lock                  # Lockfile
│   ├── Dockerfile               # Container build
│   └── index-mapping.json       # Elasticsearch field mappings
├── data/
│   ├── recipes.json             # 62K+ recipe dataset
│   └── example_output.json      # Sample API response
├── k8s/                         # Kubernetes manifests
│   ├── elasticsearch/           # ES deployment configs
│   ├── fastapi/                # API service configs
│   └── monitoring/             # Prometheus/Grafana configs
├── docker-compose.yml          # Local development stack
├── test_dataset.py            # Data validation utility
└── README.md                  # Project documentation
```

### Data Schema
**Elasticsearch Mapping** (62+ fields):
- Text fields: `recipe_title`, `description`, `ingredients`, `directions`
- Dietary flags: `is_vegan`, `is_vegetarian`, `is_gluten_free`, etc.
- Time fields: `est_prep_time_min`, `est_cook_time_min` 
- Categorization: `cuisine_list`, `difficulty`, `healthiness_score`
- Custom analyzer: `recipe_analyzer` with English stopwords

### Monitoring & Metrics
**Prometheus Metrics**:
- `dishcovery_search_requests_total` - Request counter by status code
- `dishcovery_search_duration_seconds` - Response time histogram
- `dishcovery_elasticsearch_health_status` - ES cluster health gauge
- `dishcovery_bulk_operations_total` - Bulk load operation counter

**Services**:
- API: http://localhost:8000
- Elasticsearch: http://localhost:9200  
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### Current Status
- ✅ Advanced POST search endpoint with JSON body
- ✅ Prometheus metrics collection
- 🚧 Grafana dashboards (in progress)
- ❌ Frontend (planned)
- ❓ Recipe recommendation engine (under consideration)
- ❓ Elasticsearch cluster scaling (under consideration)

### Development Notes
- Uses async/await patterns throughout for performance
- Thread pool executor for sync Elasticsearch operations
- Runtime field calculations for total cooking time
- Comprehensive error handling with proper HTTP status codes
- Health checks for both API and Elasticsearch
- Auto data loading on startup if index is empty

