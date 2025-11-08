from fastapi import FastAPI, HTTPException
from elasticsearch_client import es_client
from config import settings
from models import SearchResponse, Recipe, BulkLoadResponse, SearchRequest
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
            detail="recipes.json file not found. Expected at ../data/recipes.json"
        )
    
    start_time = time.time()
    
    try:
        # Load recipes from JSON file
        with open(recipes_file, 'r') as f:
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
            message=f"Successfully loaded {loaded_count} recipes in {total_time:.2f}s"
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
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        }
    }
    
    # Add text search if provided
    if request.query:
        query_body["query"]["bool"]["must"].append({
            "multi_match": {
                "query": request.query,
                "fields": ["recipe_title^3", "description^2", "ingredient_text", "directions_text"],
                "type": "best_fields"
            }
        })
    else:
        query_body["query"]["bool"]["must"].append({"match_all": {}})
    
    # Add cuisine filters (can be multiple)
    if request.cuisines:
        query_body["query"]["bool"]["filter"].append({
            "terms": {"cuisine_list": request.cuisines}
        })
    
    # Add difficulty filter
    if request.difficulty:
        query_body["query"]["bool"]["filter"].append({
            "term": {"difficulty": request.difficulty.value}
        })
    
    # Add prep time filter
    if request.max_prep_time:
        query_body["query"]["bool"]["filter"].append({
            "range": {"est_prep_time_min": {"lte": request.max_prep_time}}
        })
    
    # Add cook time filter
    if request.max_cook_time:
        query_body["query"]["bool"]["filter"].append({
            "range": {"est_cook_time_min": {"lte": request.max_cook_time}}
        })
    
    # Add dietary filters
    dietary_filters = [
        (request.is_vegan, "is_vegan"),
        (request.is_vegetarian, "is_vegetarian"), 
        (request.is_gluten_free, "is_gluten_free"),
        (request.is_dairy_free, "is_dairy_free"),
        (request.is_nut_free, "is_nut_free")
    ]
    
    for value, field in dietary_filters:
        if value is not None:
            query_body["query"]["bool"]["filter"].append({
                "term": {field: value}
            })
    
    # Add healthiness score filters
    if request.min_healthiness or request.max_healthiness:
        range_filter = {}
        if request.min_healthiness:
            range_filter["gte"] = request.min_healthiness
        if request.max_healthiness:
            range_filter["lte"] = request.max_healthiness
        
        query_body["query"]["bool"]["filter"].append({
            "range": {"healthiness_score": range_filter}
        })
    
    # Execute search
    result = await es_client.search_recipes(query_body)
    
    # Parse results
    recipes = []
    for hit in result["hits"]["hits"]:
        source = hit["_source"]
        recipe = Recipe(**source)
        recipes.append(recipe)
    
    return SearchResponse(
        total=result["hits"]["total"]["value"],
        recipes=recipes,
        took_ms=result["took"]
    )
