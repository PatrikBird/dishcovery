from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from elasticsearch_client import es_client
from config import settings
from models import SearchResponse, Recipe, BulkLoadResponse
from typing import Optional
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


@app.get("/search", response_model=SearchResponse)
async def search_recipes(
    q: Optional[str] = Query(None, description="Search query for recipe titles, ingredients, descriptions"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine (e.g. 'Italian', 'Asian')"),
    max_prep_time: Optional[int] = Query(None, description="Maximum prep time in minutes"),
    is_vegan: Optional[bool] = Query(None, description="Filter for vegan recipes"),
    size: int = Query(10, ge=1, le=50, description="Number of results to return")
):
    """Basic search endpoint with query parameters"""
    
    # Build Elasticsearch query
    query_body = {
        "size": size,
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        }
    }
    
    # Add text search if provided
    if q:
        query_body["query"]["bool"]["must"].append({
            "multi_match": {
                "query": q,
                "fields": ["recipe_title^3", "description^2", "ingredient_text", "directions_text"],
                "type": "best_fields"
            }
        })
    else:
        query_body["query"]["bool"]["must"].append({"match_all": {}})
    
    # Add filters
    if cuisine:
        query_body["query"]["bool"]["filter"].append({
            "term": {"cuisine_list": cuisine}
        })
    
    if max_prep_time:
        query_body["query"]["bool"]["filter"].append({
            "range": {"est_prep_time_min": {"lte": max_prep_time}}
        })
    
    if is_vegan is not None:
        query_body["query"]["bool"]["filter"].append({
            "term": {"is_vegan": is_vegan}
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
