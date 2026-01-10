from fastapi import FastAPI, HTTPException, Response, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from elasticsearch_client import es_client
from config import settings
from models import (
    Recipe,
    BulkLoadResponse,
    SearchRequest,
    Aggregations,
    AggregationBucket,
    AggregationStats,
)
import json
from typing import Optional, List
import time
import os
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

search_requests_total = Counter(
    "dishcovery_search_requests_total",
    "Total number of search requests",
    ["status_code"],
)

search_duration_seconds = Histogram(
    "dishcovery_search_duration_seconds", "Time spent processing search requests"
)

elasticsearch_health_status = Gauge(
    "dishcovery_elasticsearch_health_status",
    "Elasticsearch health status (1=green, 0.5=yellow, 0=red)",
)

bulk_operations_total = Counter(
    "dishcovery_bulk_operations_total",
    "Total number of bulk loading operations",
    ["status"],
)

AGGREGATION_CONFIGS = {
    "cuisines": {"terms": {"field": "cuisine_list.keyword", "size": 1000, "order": {"_key": "asc"}}},
    "difficulty_levels": {"terms": {"field": "difficulty.keyword", "size": 50, "order": {"_key": "asc"}}},
    "dietary_profiles": {"terms": {"field": "dietary_profile.keyword", "size": 50, "order": {"_key": "asc"}}},
    "healthiness_stats": {"stats": {"field": "healthiness_score"}},
    "prep_time_ranges": {
        "range": {
            "field": "est_prep_time_min",
            "ranges": [
                {"key": "0-15 min", "to": 15},
                {"key": "15-30 min", "from": 15, "to": 30},
                {"key": "30-60 min", "from": 30, "to": 60},
                {"key": "60+ min", "from": 60},
            ],
        }
    },
    "cook_time_ranges": {
        "range": {
            "field": "est_cook_time_min",
            "ranges": [
                {"key": "0-15 min", "to": 15},
                {"key": "15-30 min", "from": 15, "to": 30},
                {"key": "30-45 min", "from": 30, "to": 45},
                {"key": "45-60 min", "from": 45, "to": 60},
                {"key": "60-90 min", "from": 60, "to": 90},
                {"key": "90-120 min", "from": 90, "to": 120},
                {"key": "120+ min", "from": 120},
            ],
        }
    },
    "total_time_ranges": {
        "range": {
            "field": "total_time_min",
            "ranges": [
                {"key": "0-30 min", "to": 30},
                {"key": "30-60 min", "from": 30, "to": 60},
                {"key": "60-90 min", "from": 60, "to": 90},
                {"key": "90-120 min", "from": 90, "to": 120},
                {"key": "120+ min", "from": 120},
            ],
        }
    },
}


def parse_aggregations(aggs_data: dict) -> Aggregations:
    """Parse Elasticsearch aggregation results into Pydantic models"""

    def parse_bucket_agg(agg_name: str) -> Optional[List[AggregationBucket]]:
        """Helper to parse bucket aggregations (terms, ranges)"""
        if agg_name not in aggs_data:
            return None
        return [
            AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
            for bucket in aggs_data[agg_name]["buckets"]
        ]

    cuisines = parse_bucket_agg("cuisines")
    difficulty_levels = parse_bucket_agg("difficulty_levels")
    dietary_profiles = parse_bucket_agg("dietary_profiles")
    prep_time_ranges = parse_bucket_agg("prep_time_ranges")
    cook_time_ranges = parse_bucket_agg("cook_time_ranges")
    total_time_ranges = parse_bucket_agg("total_time_ranges")

    # Parse healthiness stats (special case)
    healthiness_stats = None
    if "healthiness_stats" in aggs_data:
        stats = aggs_data["healthiness_stats"]
        healthiness_stats = AggregationStats(
            min=stats.get("min"),
            max=stats.get("max"),
            avg=round(stats.get("avg", 0), 1) if stats.get("avg") else None,
            sum=stats.get("sum"),
        )

    return Aggregations(
        cuisines=cuisines,
        difficulty_levels=difficulty_levels,
        dietary_profiles=dietary_profiles,
        healthiness_stats=healthiness_stats,
        prep_time_ranges=prep_time_ranges,
        cook_time_ranges=cook_time_ranges,
        total_time_ranges=total_time_ranges,
    )


def build_search_query(request: SearchRequest) -> dict:
    """Build Elasticsearch query from search request"""
    query_body = {
        "size": request.size,
        "from": request.from_,
        "query": {"bool": {"must": []}},
        "post_filter": {"bool": {"filter": []}},
    }

    # Add aggregations and runtime mappings if requested
    if request.include_aggregations:
        query_body["runtime_mappings"] = {
            "total_time_min": {
                "type": "long",
                "script": {
                    "source": "emit((doc['est_prep_time_min'].size() > 0 ? doc['est_prep_time_min'].value : 0) + (doc['est_cook_time_min'].size() > 0 ? doc['est_cook_time_min'].value : 0))"
                },
            }
        }
        query_body["aggs"] = AGGREGATION_CONFIGS

    # Add text search to main query (affects both results and aggregations)
    if request.query:
        query_body["query"]["bool"]["must"].append(
            {
                "multi_match": {
                    "query": request.query,
                    "fields": [
                        "recipe_title^4",
                        "description^2",
                        "ingredient_text",
                        "directions_text",
                    ],
                    "type": "best_fields",
                    "fuzziness": request.fuzziness or "AUTO",
                }
            }
        )
    else:
        query_body["query"]["bool"]["must"].append({"match_all": {}})

    # Add filters to post_filter (affects results but not aggregations)
    if request.cuisines:
        query_body["post_filter"]["bool"]["filter"].append(
            {"terms": {"cuisine_list.keyword": request.cuisines}}
        )

    if request.difficulty:
        query_body["post_filter"]["bool"]["filter"].append(
            {"term": {"difficulty.keyword": request.difficulty.value}}
        )

    if request.max_prep_time:
        query_body["post_filter"]["bool"]["filter"].append(
            {"range": {"est_prep_time_min": {"lte": request.max_prep_time}}}
        )

    if request.max_cook_time:
        query_body["post_filter"]["bool"]["filter"].append(
            {"range": {"est_cook_time_min": {"lte": request.max_cook_time}}}
        )

    # Add dietary filters
    dietary_filters = [
        (request.is_vegan, "is_vegan"),
        (request.is_vegetarian, "is_vegetarian"),
        (request.is_gluten_free, "is_gluten_free"),
        (request.is_dairy_free, "is_dairy_free"),
        (request.is_nut_free, "is_nut_free"),
    ]

    for value, field in dietary_filters:
        if value is not None:
            query_body["post_filter"]["bool"]["filter"].append({"term": {field: value}})

    # Add healthiness score filters
    if request.min_healthiness or request.max_healthiness:
        range_filter = {}
        if request.min_healthiness:
            range_filter["gte"] = request.min_healthiness
        if request.max_healthiness:
            range_filter["lte"] = request.max_healthiness

        query_body["post_filter"]["bool"]["filter"].append(
            {"range": {"healthiness_score": range_filter}}
        )

    # Clean up empty post_filter
    if not query_body["post_filter"]["bool"]["filter"]:
        del query_body["post_filter"]

    return query_body


app = FastAPI(
    title=settings.API_TITLE,
    description="Recipe search service powered by Elasticsearch",
    version=settings.API_VERSION,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    """Load data on startup if index is empty"""
    import asyncio

    # Give ES a moment to fully initialize after health check
    await asyncio.sleep(5)

    try:
        # Check if index exists and has data
        index_exists = await es_client.index_exists()
        if not index_exists:
            print("Index doesn't exist, loading initial data...")
            await load_initial_data()
        else:
            # Check if index has data
            result = await es_client.search_recipes({"size": 0})
            total_docs = result["hits"]["total"]["value"]
            if total_docs == 0:
                print("Index exists but is empty, loading initial data...")
                await load_initial_data()
            else:
                print(f"Index already has {total_docs} documents")
    except Exception as e:
        print(f"Startup data loading failed: {e}")


async def load_initial_data():
    """Load initial recipe data with proper index mapping"""
    import os

    # First, create index with proper mapping
    mapping_file = "index-mapping.json"
    if os.path.exists(mapping_file):
        with open(mapping_file, "r") as f:
            mapping_data = json.load(f)
        await es_client.create_index_with_mapping(mapping_data)
        print("Index created with proper mapping")
    else:
        print(f"Mapping file not found at {mapping_file}")

    # Then load data
    recipes_file = "../data/recipes_cleaned.json"
    if os.path.exists(recipes_file):
        with open(recipes_file, "r") as f:
            recipes_data = json.load(f)
        result = await es_client.bulk_index_recipes(recipes_data)
        print(f"Loaded {result[0]} recipes successfully")
    else:
        print(f"Data file not found at {recipes_file}")


@app.get("/")
async def root(request: Request):
    # Get initial aggregations for the filter sidebar
    try:
        # Build a basic query to get aggregations
        query_body = {
            "size": 0,  # We only want aggregations, not results
            "query": {"match_all": {}},
            "runtime_mappings": {
                "total_time_min": {
                    "type": "long",
                    "script": {
                        "source": "emit((doc['est_prep_time_min'].size() > 0 ? doc['est_prep_time_min'].value : 0) + (doc['est_cook_time_min'].size() > 0 ? doc['est_cook_time_min'].value : 0))"
                    },
                }
            },
            "aggs": AGGREGATION_CONFIGS,
        }

        result = await es_client.search_recipes(query_body)
        aggregations = None
        if "aggregations" in result:
            aggregations = parse_aggregations(result["aggregations"])
    except Exception as e:
        # If aggregation fails, we'll just not pass aggregations
        print(f"Failed to load initial aggregations: {e}")
        aggregations = None

    # Initialize empty current_filters for page load
    current_filters = {
        "cuisines": [],
        "difficulty": None,
        "is_vegan": None,
        "is_vegetarian": None,
        "is_gluten_free": None,
        "is_dairy_free": None,
        "is_nut_free": None,
        "max_prep_time": None,
        "max_cook_time": None,
        "min_healthiness": None,
        "max_healthiness": None,
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": settings.API_VERSION,
            "aggregations": aggregations,
            "current_filters": current_filters,
        },
    )


@app.get("/health")
async def health_check():
    es_health = await es_client.health_check()
    index_exists = await es_client.index_exists()

    # Update Elasticsearch health metric
    if "status" in es_health:
        if es_health["status"] == "green":
            elasticsearch_health_status.set(1)
        elif es_health["status"] == "yellow":
            elasticsearch_health_status.set(0.5)
        else:  # red or error
            elasticsearch_health_status.set(0)

    return {
        "status": "healthy",
        "service": "dishcovery-api",
        "elasticsearch": es_health,
        "recipes_index_exists": index_exists,
    }


@app.post("/bulk-load", response_model=BulkLoadResponse)
async def bulk_load_recipes():
    """Load all recipes from data/recipes.json into Elasticsearch"""

    recipes_file = "../data/recipes_cleaned.json"
    if not os.path.exists(recipes_file):
        raise HTTPException(
            status_code=404,
            detail="recipes_cleaned.json file not found. Expected at ../data/recipes_cleaned.json",
        )

    start_time = time.time()

    try:
        with open(recipes_file, "r") as f:
            recipes_data = json.load(f)

        result = await es_client.bulk_index_recipes(recipes_data)

        end_time = time.time()
        total_time = end_time - start_time

        # Parse bulk result
        loaded_count = result[0] if result else 0
        failed_count = len(result[1]) if len(result) > 1 else 0

        # Record successful bulk operation
        bulk_operations_total.labels(status="success").inc()

        return BulkLoadResponse(
            loaded_count=loaded_count,
            failed_count=failed_count,
            total_time_seconds=round(total_time, 2),
            message=f"Successfully loaded {loaded_count} recipes in {total_time:.2f}s",
        )

    except Exception as e:
        bulk_operations_total.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=f"Bulk loading failed: {str(e)}")


@app.post("/search", response_class=HTMLResponse)
async def search_recipes(
    request: Request,
    query: str = Form(""),
    size: int = Form(10),
    from_: int = Form(0, alias="from"),
    append: Optional[str] = Form(None),
    cuisines: Optional[List[str]] = Form(None),
    difficulty: Optional[str] = Form(None),
    is_vegan: Optional[str] = Form(None),
    is_vegetarian: Optional[str] = Form(None),
    is_gluten_free: Optional[str] = Form(None),
    is_dairy_free: Optional[str] = Form(None),
    is_nut_free: Optional[str] = Form(None),
    max_prep_time: Optional[str] = Form(None),
    max_cook_time: Optional[str] = Form(None),
    min_healthiness: Optional[str] = Form(None),
    max_healthiness: Optional[str] = Form(None),
):
    """Search recipes with form data from HTMX including filters"""

    start_time = time.time()
    status_code = 200
    is_append = append == "true"

    try:
        # Convert string boolean values to actual booleans
        def parse_bool(value):
            if value == "true":
                return True
            elif value == "false":
                return False
            return None

        # Convert string integer values to actual integers
        def parse_int(value):
            if value and value.strip():
                try:
                    return int(value.strip())
                except (ValueError, TypeError):
                    return None
            return None

        # Build SearchRequest object from form data
        search_request = SearchRequest(
            query=query.strip() if query else "",
            size=min(size, 50),  # Limit max size for performance
            from_=max(from_, 0),  # Ensure non-negative offset
            include_aggregations=not is_append,  # Skip aggregations for append requests
            cuisines=cuisines if cuisines else None,
            difficulty=difficulty if difficulty else None,
            is_vegan=parse_bool(is_vegan),
            is_vegetarian=parse_bool(is_vegetarian),
            is_gluten_free=parse_bool(is_gluten_free),
            is_dairy_free=parse_bool(is_dairy_free),
            is_nut_free=parse_bool(is_nut_free),
            max_prep_time=parse_int(max_prep_time),
            max_cook_time=parse_int(max_cook_time),
            min_healthiness=parse_int(min_healthiness)
            if parse_int(min_healthiness) and parse_int(min_healthiness) > 16
            else None,
            max_healthiness=parse_int(max_healthiness)
            if parse_int(max_healthiness) and parse_int(max_healthiness) < 100
            else None,
        )

        query_body = build_search_query(search_request)
        result = await es_client.search_recipes(query_body)

        recipes = [Recipe(**hit["_source"]) for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]

        # For append requests, return just the additional cards
        if is_append:
            return templates.TemplateResponse(
                "partials/search_results_append.html",
                {
                    "request": request,
                    "total": total,
                    "recipes": recipes,
                    "from_": search_request.from_,
                    "size": search_request.size,
                },
            )

        # Parse aggregations if available
        aggregations = None
        if "aggregations" in result:
            aggregations = parse_aggregations(result["aggregations"])

        # Build current filter state for template
        current_filters = {
            "cuisines": cuisines or [],
            "difficulty": difficulty,
            "is_vegan": parse_bool(is_vegan),
            "is_vegetarian": parse_bool(is_vegetarian),
            "is_gluten_free": parse_bool(is_gluten_free),
            "is_dairy_free": parse_bool(is_dairy_free),
            "is_nut_free": parse_bool(is_nut_free),
            "max_prep_time": parse_int(max_prep_time),
            "max_cook_time": parse_int(max_cook_time),
            "min_healthiness": parse_int(min_healthiness),
            "max_healthiness": parse_int(max_healthiness),
        }

        return templates.TemplateResponse(
            "partials/search_response.html",
            {
                "request": request,
                "total": total,
                "recipes": recipes,
                "took_ms": result["took"],
                "aggregations": aggregations,
                "query": search_request.query,  # Pass back the query for display
                "current_filters": current_filters,  # Pass current filter state
                "from_": search_request.from_,
                "size": search_request.size,
            },
        )

    except Exception as e:
        status_code = 500
        # Return error as HTML fragment for HTMX
        return f"""
        <div class="error-message" style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px; margin: 10px 0;">
            <strong>Search Error:</strong> {str(e)}
        </div>
        """
    finally:
        # Record metrics
        duration = time.time() - start_time
        search_duration_seconds.observe(duration)
        search_requests_total.labels(status_code=status_code).inc()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
