from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CookSpeed(str, Enum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"


class SearchRequest(BaseModel):
    """Request model for recipe search - all fields are optional for maximum flexibility"""

    query: Optional[str] = Field(
        None,
        description="Text search across recipe titles, descriptions, ingredients, and directions",
        example="pasta",
    )
    fuzziness: Optional[str] = Field(
        "AUTO",
        description="Fuzzy matching level: 0 (exact), 1, 2, or AUTO (recommended)",
        example="AUTO",
    )

    cuisines: Optional[List[str]] = Field(
        None,
        description="Filter by one or more cuisine types",
        example=["italian", "asian"],
    )

    difficulty: Optional[DifficultyLevel] = Field(
        None, description="Recipe difficulty level"
    )
    max_prep_time: Optional[int] = Field(
        None, ge=0, description="Maximum prep time in minutes", example=30
    )
    max_cook_time: Optional[int] = Field(
        None, ge=0, description="Maximum cook time in minutes", example=60
    )

    is_vegan: Optional[bool] = Field(None, description="Filter for vegan recipes")
    is_vegetarian: Optional[bool] = Field(
        None, description="Filter for vegetarian recipes"
    )
    is_gluten_free: Optional[bool] = Field(
        None, description="Filter for gluten-free recipes"
    )
    is_dairy_free: Optional[bool] = Field(
        None, description="Filter for dairy-free recipes"
    )
    is_nut_free: Optional[bool] = Field(None, description="Filter for nut-free recipes")
    is_kosher: Optional[bool] = Field(None, description="Filter for kosher recipes")
    is_halal: Optional[bool] = Field(None, description="Filter for halal recipes")

    min_healthiness: Optional[int] = Field(
        None, ge=0, le=100, description="Minimum healthiness score (0-100)", example=70
    )
    max_healthiness: Optional[int] = Field(
        None, ge=0, le=100, description="Maximum healthiness score (0-100)", example=90
    )

    size: int = Field(
        10,
        ge=0,
        le=100,
        description="Number of results to return (0 for aggregations only)",
        example=10,
    )
    from_: int = Field(
        0, ge=0, description="Offset for pagination (0-based)", alias="from", example=0
    )

    # Aggregations control
    include_aggregations: bool = Field(
        False, description="Include aggregation data for filtering and insights"
    )


class Recipe(BaseModel):
    """Recipe response model"""

    recipe_title: str
    description: Optional[str] = None
    cuisine_list: Optional[List[str]] = None
    difficulty: Optional[str] = None
    est_prep_time_min: Optional[int] = None
    est_cook_time_min: Optional[int] = None
    is_vegan: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    is_gluten_free: Optional[bool] = None
    healthiness_score: Optional[int] = None
    ingredients_raw: Optional[List[str]] = None
    directions_raw: Optional[List[str]] = None


class AggregationBucket(BaseModel):
    """Single aggregation bucket (e.g., one cuisine type)"""

    key: str = Field(description="The bucket key (e.g., 'italian')")
    doc_count: int = Field(description="Number of documents in this bucket")


class AggregationStats(BaseModel):
    """Statistics aggregation results"""

    min: Optional[float] = None
    max: Optional[float] = None
    avg: Optional[float] = None
    sum: Optional[float] = None


class Aggregations(BaseModel):
    """Aggregation results for search facets and insights"""

    cuisines: Optional[List[AggregationBucket]] = Field(
        None, description="Recipe count by cuisine"
    )
    difficulty_levels: Optional[List[AggregationBucket]] = Field(
        None, description="Recipe count by difficulty"
    )
    dietary_profiles: Optional[List[AggregationBucket]] = Field(
        None, description="Recipe count by dietary profile (vegan, vegetarian, etc.)"
    )
    is_vegetarian_count: Optional[int] = Field(
        None, description="Count of vegetarian recipes"
    )
    is_dairy_free_count: Optional[int] = Field(
        None, description="Count of dairy-free recipes"
    )
    healthiness_stats: Optional[AggregationStats] = Field(
        None, description="Healthiness score statistics"
    )
    prep_time_ranges: Optional[List[AggregationBucket]] = Field(
        None, description="Recipe count by prep time ranges"
    )
    cook_time_ranges: Optional[List[AggregationBucket]] = Field(
        None, description="Recipe count by cooking time ranges"
    )
    total_time_ranges: Optional[List[AggregationBucket]] = Field(
        None, description="Recipe count by total time (prep + cook) ranges"
    )


class SearchResponse(BaseModel):
    """Search results response"""

    total: int = Field(description="Total number of matching recipes")
    recipes: List[Recipe] = Field(description="Array of recipe results")
    took_ms: int = Field(description="Search execution time in milliseconds")
    aggregations: Optional[Aggregations] = Field(
        None, description="Aggregation results for filtering and insights"
    )


class BulkLoadResponse(BaseModel):
    """Response for bulk data loading"""

    loaded_count: int
    failed_count: int
    total_time_seconds: float
    message: str
