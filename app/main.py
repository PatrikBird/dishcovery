from fastapi import FastAPI, HTTPException
from elasticsearch_client import es_client
from config import settings
from models import (
    SearchResponse,
    Recipe,
    BulkLoadResponse,
    SearchRequest,
    Aggregations,
    AggregationBucket,
    AggregationStats,
)
import json
import time
import os

app = FastAPI(
    title=settings.API_TITLE,
    description="Recipe search service powered by Elasticsearch",
    version=settings.API_VERSION,
)


@app.get("/")
async def root():
    return {"message": "Welcome to Dishcovery Recipe Search API"}


@app.get("/health")
async def health_check():
    es_health = await es_client.health_check()
    index_exists = await es_client.index_exists()

    return {
        "status": "healthy",
        "service": "dishcovery-api",
        "elasticsearch": es_health,
        "recipes_index_exists": index_exists,
    }


@app.post("/bulk-load", response_model=BulkLoadResponse)
async def bulk_load_recipes():
    """Load all recipes from data/recipes.json into Elasticsearch"""

    # Check if recipes file exists
    recipes_file = "../data/recipes.json"
    if not os.path.exists(recipes_file):
        raise HTTPException(
            status_code=404,
            detail="recipes.json file not found. Expected at ../data/recipes.json",
        )

    start_time = time.time()

    try:
        # Load recipes from JSON file
        with open(recipes_file, "r") as f:
            recipes_data = json.load(f)

        # Bulk index to Elasticsearch
        result = await es_client.bulk_index_recipes(recipes_data)

        end_time = time.time()
        total_time = end_time - start_time

        # Parse bulk result
        loaded_count = result[0] if result else 0
        failed_count = len(result[1]) if len(result) > 1 else 0

        return BulkLoadResponse(
            loaded_count=loaded_count,
            failed_count=failed_count,
            total_time_seconds=round(total_time, 2),
            message=f"Successfully loaded {loaded_count} recipes in {total_time:.2f}s",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk loading failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_recipes(request: SearchRequest):
    """Search recipes with flexible filtering options"""

    # Build Elasticsearch query
    query_body = {
        "size": request.size,
        "from": request.from_,
        "query": {"bool": {"must": [], "filter": []}},
    }

    # Add aggregations if requested
    if request.include_aggregations:
        # Add runtime field for total time calculation
        query_body["runtime_mappings"] = {
            "total_time_min": {
                "type": "long",
                "script": {
                    "source": "emit((doc['est_prep_time_min'].size() > 0 ? doc['est_prep_time_min'].value : 0) + (doc['est_cook_time_min'].size() > 0 ? doc['est_cook_time_min'].value : 0))"
                },
            }
        }

        query_body["aggs"] = {
            "cuisines": {"terms": {"field": "cuisine_list", "size": 20}},
            "difficulty_levels": {"terms": {"field": "difficulty", "size": 10}},
            "dietary_profiles": {"terms": {"field": "dietary_profile", "size": 15}},
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

    # Add text search if provided
    if request.query:
        query_body["query"]["bool"]["must"].append(
            {
                "multi_match": {
                    "query": request.query,
                    "fields": [
                        "recipe_title^4",  # Highest boost for exact title matches
                        "description^2",
                        "ingredient_text",
                        "directions_text",
                    ],
                    "type": "best_fields",
                    "fuzziness": request.fuzziness
                    or "AUTO",  # User-controlled fuzziness
                }
            }
        )
    else:
        query_body["query"]["bool"]["must"].append({"match_all": {}})

    # Add cuisine filters (can be multiple)
    if request.cuisines:
        query_body["query"]["bool"]["filter"].append(
            {"terms": {"cuisine_list": request.cuisines}}
        )

    # Add difficulty filter
    if request.difficulty:
        query_body["query"]["bool"]["filter"].append(
            {"term": {"difficulty": request.difficulty.value}}
        )

    # Add prep time filter
    if request.max_prep_time:
        query_body["query"]["bool"]["filter"].append(
            {"range": {"est_prep_time_min": {"lte": request.max_prep_time}}}
        )

    # Add cook time filter
    if request.max_cook_time:
        query_body["query"]["bool"]["filter"].append(
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
            query_body["query"]["bool"]["filter"].append({"term": {field: value}})

    # Add healthiness score filters
    if request.min_healthiness or request.max_healthiness:
        range_filter = {}
        if request.min_healthiness:
            range_filter["gte"] = request.min_healthiness
        if request.max_healthiness:
            range_filter["lte"] = request.max_healthiness

        query_body["query"]["bool"]["filter"].append(
            {"range": {"healthiness_score": range_filter}}
        )

    # Execute search
    result = await es_client.search_recipes(query_body)

    # Parse results
    recipes = []
    for hit in result["hits"]["hits"]:
        source = hit["_source"]
        recipe = Recipe(**source)
        recipes.append(recipe)

    # Parse aggregations if included
    aggregations = None
    if request.include_aggregations and "aggregations" in result:
        aggs_data = result["aggregations"]

        # Parse cuisine aggregation
        cuisines = None
        if "cuisines" in aggs_data:
            cuisines = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in aggs_data["cuisines"]["buckets"]
            ]

        # Parse difficulty levels
        difficulty_levels = None
        if "difficulty_levels" in aggs_data:
            difficulty_levels = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in aggs_data["difficulty_levels"]["buckets"]
            ]

        # Parse dietary profiles
        dietary_profiles = None
        if "dietary_profiles" in aggs_data:
            dietary_profiles = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in aggs_data["dietary_profiles"]["buckets"]
            ]

        # Parse healthiness stats
        healthiness_stats = None
        if "healthiness_stats" in aggs_data:
            stats = aggs_data["healthiness_stats"]
            healthiness_stats = AggregationStats(
                min=stats.get("min"),
                max=stats.get("max"),
                avg=round(stats.get("avg", 0), 1) if stats.get("avg") else None,
                sum=stats.get("sum"),
            )

        # Parse prep time ranges
        prep_time_ranges = None
        if "prep_time_ranges" in aggs_data:
            prep_time_ranges = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in aggs_data["prep_time_ranges"]["buckets"]
            ]

        # Parse cook time ranges
        cook_time_ranges = None
        if "cook_time_ranges" in aggs_data:
            cook_time_ranges = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in aggs_data["cook_time_ranges"]["buckets"]
            ]

        # Parse total time ranges
        total_time_ranges = None
        if "total_time_ranges" in aggs_data:
            total_time_ranges = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in aggs_data["total_time_ranges"]["buckets"]
            ]

        aggregations = Aggregations(
            cuisines=cuisines,
            difficulty_levels=difficulty_levels,
            dietary_profiles=dietary_profiles,
            healthiness_stats=healthiness_stats,
            prep_time_ranges=prep_time_ranges,
            cook_time_ranges=cook_time_ranges,
            total_time_ranges=total_time_ranges,
        )

    return SearchResponse(
        total=result["hits"]["total"]["value"],
        recipes=recipes,
        took_ms=result["took"],
        aggregations=aggregations,
    )
